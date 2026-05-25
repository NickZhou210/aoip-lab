#!/usr/bin/env python3
"""Derive an RTP-to-reference-time anchor from captured RTP packets.

This is a learning tool. It uses pcap packet timestamps as the observable
reference time because the lab sender is not yet truly PTP-locked.
"""

from __future__ import annotations

import argparse
import json
import socket
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG = REPO_ROOT / "project2_rtp_audio_stream" / "config" / "streams.json"


@dataclass
class RtpPoint:
    capture_time_s: float
    rtp_timestamp: int
    sequence: int
    ssrc: int


@dataclass
class StreamAnchor:
    name: str
    group: str
    port: int
    first: RtpPoint | None = None
    last: RtpPoint | None = None
    packets: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Derive RTP/PTP timing anchors from a pcap")
    parser.add_argument("pcap", help="pcap file containing configured RTP streams")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--playout-latency-ms", type=float, default=50.0, help="receiver latency model")
    parser.add_argument("--limit", type=int, default=16, help="number of streams to print")
    return parser.parse_args()


def read_pcap_header(handle: BinaryIO) -> tuple[str, int, float]:
    header = handle.read(24)
    if len(header) != 24:
        raise ValueError("pcap global header is incomplete")

    magic = header[:4]
    if magic == b"\xd4\xc3\xb2\xa1":
        return "<", struct.unpack("<IHHIIII", header)[6], 1_000_000.0
    if magic == b"\xa1\xb2\xc3\xd4":
        return ">", struct.unpack(">IHHIIII", header)[6], 1_000_000.0
    if magic == b"\x4d\x3c\xb2\xa1":
        return "<", struct.unpack("<IHHIIII", header)[6], 1_000_000_000.0
    if magic == b"\xa1\xb2\x3c\x4d":
        return ">", struct.unpack(">IHHIIII", header)[6], 1_000_000_000.0

    raise ValueError("unsupported pcap magic")


def read_packets(handle: BinaryIO, endian: str, fraction_scale: float) -> Iterator[tuple[float, bytes]]:
    while True:
        packet_header = handle.read(16)
        if not packet_header:
            return
        if len(packet_header) != 16:
            raise ValueError("pcap packet header is incomplete")

        seconds, fraction, included_length, _ = struct.unpack(f"{endian}IIII", packet_header)
        packet = handle.read(included_length)
        if len(packet) != included_length:
            raise ValueError("pcap packet data is incomplete")

        yield seconds + (fraction / fraction_scale), packet


def ethernet_payload(packet: bytes) -> bytes | None:
    if len(packet) < 14:
        return None

    offset = 14
    ethertype = struct.unpack("!H", packet[12:14])[0]
    while ethertype in (0x8100, 0x88A8):
        if len(packet) < offset + 4:
            return None
        ethertype = struct.unpack("!H", packet[offset + 2 : offset + 4])[0]
        offset += 4

    if ethertype != 0x0800:
        return None
    return packet[offset:]


def ipv4_udp_payload(ip_packet: bytes) -> tuple[str, int, bytes] | None:
    if len(ip_packet) < 28:
        return None

    version = ip_packet[0] >> 4
    ihl = (ip_packet[0] & 0x0F) * 4
    if version != 4 or len(ip_packet) < ihl + 8:
        return None
    if ip_packet[9] != 17:
        return None

    destination_ip = socket.inet_ntoa(ip_packet[16:20])
    udp_start = ihl
    _, destination_port, udp_length, _ = struct.unpack("!HHHH", ip_packet[udp_start : udp_start + 8])
    payload_start = udp_start + 8
    payload_end = payload_start + max(0, udp_length - 8)
    return destination_ip, destination_port, ip_packet[payload_start:payload_end]


def parse_rtp_point(capture_time_s: float, payload: bytes) -> RtpPoint | None:
    if len(payload) < 12:
        return None

    first, _second, sequence, timestamp, ssrc = struct.unpack("!BBHII", payload[:12])
    version = first >> 6
    if version != 2:
        return None

    return RtpPoint(capture_time_s=capture_time_s, rtp_timestamp=timestamp, sequence=sequence, ssrc=ssrc)


def load_anchors(config_path: Path) -> tuple[list[StreamAnchor], int]:
    with config_path.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)

    anchors = [
        StreamAnchor(name=stream["name"], group=stream["group"], port=stream["port"])
        for stream in plan["streams"]
    ]
    return anchors, int(plan["sample_rate_hz"])


def main() -> None:
    args = parse_args()
    pcap_path = Path(args.pcap)
    anchors, sample_rate = load_anchors(Path(args.config))
    by_destination = {(anchor.group, anchor.port): anchor for anchor in anchors}

    with pcap_path.open("rb") as handle:
        endian, linktype, fraction_scale = read_pcap_header(handle)
        if linktype != 1:
            raise SystemExit(f"unsupported pcap linktype {linktype}; expected Ethernet linktype 1")

        for capture_time_s, packet in read_packets(handle, endian, fraction_scale):
            payload = ethernet_payload(packet)
            if payload is None:
                continue
            udp = ipv4_udp_payload(payload)
            if udp is None:
                continue

            destination_ip, destination_port, udp_payload = udp
            anchor = by_destination.get((destination_ip, destination_port))
            if anchor is None:
                continue

            point = parse_rtp_point(capture_time_s, udp_payload)
            if point is None:
                continue

            if anchor.first is None:
                anchor.first = point
            anchor.last = point
            anchor.packets += 1

    print("RTP to reference-time anchor model")
    print(f"capture:            {pcap_path}")
    print(f"sample_rate:        {sample_rate} Hz")
    print(f"playout_latency_ms: {args.playout_latency_ms:g}")
    print()
    print(
        "stream group          port packets "
        "rtp_anchor capture_anchor_s media_span_ms capture_span_ms "
        "span_error_ms first_playout_s"
    )

    printed = 0
    for anchor in anchors:
        if printed >= args.limit:
            break
        if anchor.first is None or anchor.last is None:
            continue

        rtp_span = (anchor.last.rtp_timestamp - anchor.first.rtp_timestamp) % (2**32)
        media_span_ms = rtp_span * 1000 / sample_rate
        capture_span_ms = (anchor.last.capture_time_s - anchor.first.capture_time_s) * 1000
        span_error_ms = capture_span_ms - media_span_ms
        first_playout_s = anchor.first.capture_time_s + (args.playout_latency_ms / 1000)

        print(
            f"{anchor.name:9} "
            f"{anchor.group:14} "
            f"{anchor.port:<5} "
            f"{anchor.packets:<7} "
            f"{anchor.first.rtp_timestamp:<10} "
            f"{anchor.first.capture_time_s:.6f} "
            f"{media_span_ms:13.3f} "
            f"{capture_span_ms:15.3f} "
            f"{span_error_ms:13.3f} "
            f"{first_playout_s:.6f}"
        )
        printed += 1

    print()
    print("Timing rule:")
    print("scheduled_playout_time = reference_anchor_time + ((rtp_timestamp - rtp_anchor) / sample_rate) + latency")
    print()
    print("Important limitation:")
    print("This script uses pcap capture timestamps as the observable reference time.")
    print("A production AES67 sender/receiver must use a real PTP-disciplined media clock.")


if __name__ == "__main__":
    main()
