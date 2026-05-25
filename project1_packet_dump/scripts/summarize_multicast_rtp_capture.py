#!/usr/bin/env python3
"""Summarize configured multicast RTP packets from a pcap file."""

from __future__ import annotations

import argparse
import json
import socket
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG = REPO_ROOT / "project2_rtp_audio_stream" / "config" / "streams.json"


@dataclass
class StreamStats:
    name: str
    group: str
    port: int
    packets: int = 0
    sources: set[str] = field(default_factory=set)
    payload_lengths: set[int] = field(default_factory=set)
    rtp_payload_lengths: set[int] = field(default_factory=set)
    payload_types: set[int] = field(default_factory=set)
    ssrcs: set[int] = field(default_factory=set)
    first_sequence: int | None = None
    last_sequence: int | None = None
    first_timestamp: int | None = None
    last_timestamp: int | None = None
    sequence_breaks: int = 0
    timestamp_breaks: int = 0

    def add(self, source: str, udp_payload: bytes, expected_timestamp_step: int) -> None:
        self.packets += 1
        self.sources.add(source)
        self.payload_lengths.add(len(udp_payload))

        if len(udp_payload) < 12:
            return

        first, second, sequence, timestamp, ssrc = struct.unpack("!BBHII", udp_payload[:12])
        version = first >> 6
        if version != 2:
            return

        self.payload_types.add(second & 0x7F)
        self.ssrcs.add(ssrc)
        self.rtp_payload_lengths.add(len(udp_payload) - 12)

        if self.last_sequence is not None and ((sequence - self.last_sequence) % 65536) != 1:
            self.sequence_breaks += 1
        if self.last_timestamp is not None and ((timestamp - self.last_timestamp) % (2**32)) != expected_timestamp_step:
            self.timestamp_breaks += 1

        if self.first_sequence is None:
            self.first_sequence = sequence
        if self.first_timestamp is None:
            self.first_timestamp = timestamp

        self.last_sequence = sequence
        self.last_timestamp = timestamp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize configured multicast RTP from pcap")
    parser.add_argument("pcap", help="pcap file captured with tcpdump")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    return parser.parse_args()


def read_pcap_header(handle: BinaryIO) -> tuple[str, int]:
    header = handle.read(24)
    if len(header) != 24:
        raise ValueError("pcap global header is incomplete")

    magic = header[:4]
    if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
        endian = "<"
    elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
        endian = ">"
    else:
        raise ValueError("unsupported pcap magic")

    _, _, _, _, _, _, linktype = struct.unpack(f"{endian}IHHIIII", header)
    return endian, linktype


def read_packets(handle: BinaryIO, endian: str) -> bytes:
    while True:
        packet_header = handle.read(16)
        if not packet_header:
            return
        if len(packet_header) != 16:
            raise ValueError("pcap packet header is incomplete")
        _, _, included_length, _ = struct.unpack(f"{endian}IIII", packet_header)
        packet = handle.read(included_length)
        if len(packet) != included_length:
            raise ValueError("pcap packet data is incomplete")
        yield packet


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


def ipv4_udp_payload(ip_packet: bytes) -> tuple[str, str, int, int, bytes] | None:
    if len(ip_packet) < 20:
        return None

    version = ip_packet[0] >> 4
    ihl = (ip_packet[0] & 0x0F) * 4
    if version != 4 or len(ip_packet) < ihl + 8:
        return None

    protocol = ip_packet[9]
    if protocol != 17:
        return None

    source_ip = socket.inet_ntoa(ip_packet[12:16])
    dest_ip = socket.inet_ntoa(ip_packet[16:20])
    udp_start = ihl
    source_port, dest_port, udp_length, _ = struct.unpack("!HHHH", ip_packet[udp_start : udp_start + 8])
    payload_start = udp_start + 8
    payload_end = payload_start + max(0, udp_length - 8)
    return source_ip, dest_ip, source_port, dest_port, ip_packet[payload_start:payload_end]


def load_stats(config_path: Path) -> tuple[list[StreamStats], int]:
    with config_path.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)

    stats = [
        StreamStats(name=stream["name"], group=stream["group"], port=stream["port"])
        for stream in plan["streams"]
    ]
    return stats, int(plan["samples_per_packet"])


def format_set(values: set[int] | set[str]) -> str:
    if not values:
        return "-"
    if all(isinstance(value, int) for value in values):
        return ",".join(str(value) for value in sorted(values))
    return ",".join(str(value) for value in sorted(values))


def main() -> None:
    args = parse_args()
    pcap_path = Path(args.pcap)
    stats, timestamp_step = load_stats(Path(args.config))
    by_destination = {(stat.group, stat.port): stat for stat in stats}

    total_udp = 0
    matched_udp = 0

    with pcap_path.open("rb") as handle:
        endian, linktype = read_pcap_header(handle)
        if linktype != 1:
            raise SystemExit(f"unsupported pcap linktype {linktype}; expected Ethernet linktype 1")

        for packet in read_packets(handle, endian):
            payload = ethernet_payload(packet)
            if payload is None:
                continue
            udp = ipv4_udp_payload(payload)
            if udp is None:
                continue
            source_ip, dest_ip, _source_port, dest_port, udp_payload = udp
            total_udp += 1

            stat = by_destination.get((dest_ip, dest_port))
            if stat is None:
                continue
            matched_udp += 1
            stat.add(source_ip, udp_payload, timestamp_step)

    print("Multicast RTP capture summary")
    print(f"capture: {pcap_path}")
    print(f"configured_streams: {len(stats)}")
    print(f"udp_packets_seen: {total_udp}")
    print(f"configured_rtp_packets: {matched_udp}")
    print()
    print("stream group          port packets udp_payload rtp_payload pt seq_breaks ts_breaks sources")

    passed = 0
    for stat in stats:
        if (
            stat.packets > 0
            and stat.payload_lengths == {780}
            and stat.rtp_payload_lengths == {768}
            and stat.payload_types == {96}
            and stat.sequence_breaks == 0
            and stat.timestamp_breaks == 0
        ):
            passed += 1

        print(
            f"{stat.name:9} "
            f"{stat.group:14} "
            f"{stat.port:<5} "
            f"{stat.packets:<7} "
            f"{format_set(stat.payload_lengths):11} "
            f"{format_set(stat.rtp_payload_lengths):11} "
            f"{format_set(stat.payload_types):2} "
            f"{stat.sequence_breaks:<10} "
            f"{stat.timestamp_breaks:<9} "
            f"{format_set(stat.sources)}"
        )

    print()
    if passed == len(stats):
        print(f"PASS: {passed} configured multicast RTP streams found")
    else:
        raise SystemExit(f"FAIL: {passed}/{len(stats)} configured multicast RTP streams passed")


if __name__ == "__main__":
    main()
