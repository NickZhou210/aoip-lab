#!/usr/bin/env python3
"""Monitor RTP headers from all configured streams."""

from __future__ import annotations

import argparse
import ipaddress
import json
import selectors
import socket
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR.parents[0] / "config" / "streams.json"


@dataclass
class StreamStats:
    stream: dict
    packet_count: int = 0
    first_sequence: int | None = None
    last_sequence: int | None = None
    first_timestamp: int | None = None
    last_timestamp: int | None = None
    ssrcs: set[int] = field(default_factory=set)
    payload_sizes: set[int] = field(default_factory=set)
    delta_sequences: set[int] = field(default_factory=set)
    delta_timestamps: set[int] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor all configured RTP streams")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--host", default="127.0.0.1", help="address or multicast group to listen on")
    parser.add_argument("--count", type=int, default=20, help="packets to collect per stream")
    parser.add_argument("--timeout", type=float, default=5.0, help="overall monitor timeout in seconds")
    parser.add_argument("--iface-ip", default="10.211.55.6", help="local interface IP for multicast joins")
    return parser.parse_args()


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def open_rtp_socket(address: str, port: int, iface_ip: str) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setblocking(False)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    if ipaddress.ip_address(address).is_multicast:
        sock.bind(("", port))
        membership = struct.pack("=4s4s", socket.inet_aton(address), socket.inet_aton(iface_ip))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    else:
        sock.bind((address, port))

    return sock


def parse_rtp_header(packet: bytes) -> dict[str, int]:
    if len(packet) < 12:
        raise ValueError("packet is too short to contain an RTP header")

    first, second, sequence, timestamp, ssrc = struct.unpack("!BBHII", packet[:12])
    return {
        "version": first >> 6,
        "payload_type": second & 0x7F,
        "sequence": sequence,
        "timestamp": timestamp,
        "ssrc": ssrc,
        "payload_bytes": len(packet) - 12,
    }


def complete(stats_by_id: dict[int, StreamStats], target_count: int) -> bool:
    return all(stats.packet_count >= target_count for stats in stats_by_id.values())


def update_stats(stats: StreamStats, header: dict[str, int], plan: dict) -> None:
    stream = stats.stream

    if header["version"] != 2:
        stats.errors.append(f"version={header['version']}")
    if header["payload_type"] != stream["payload_type"]:
        stats.errors.append(f"payload_type={header['payload_type']}")
    if header["payload_bytes"] != stream["payload_bytes"]:
        stats.errors.append(f"payload_bytes={header['payload_bytes']}")

    if stats.last_sequence is not None:
        delta_sequence = (header["sequence"] - stats.last_sequence) % 65536
        stats.delta_sequences.add(delta_sequence)
        if delta_sequence != 1:
            stats.errors.append(f"delta_seq={delta_sequence}")

    if stats.last_timestamp is not None:
        delta_timestamp = (header["timestamp"] - stats.last_timestamp) % (2**32)
        stats.delta_timestamps.add(delta_timestamp)
        if delta_timestamp != plan["samples_per_packet"]:
            stats.errors.append(f"delta_ts={delta_timestamp}")

    if stats.first_sequence is None:
        stats.first_sequence = header["sequence"]
    if stats.first_timestamp is None:
        stats.first_timestamp = header["timestamp"]

    stats.last_sequence = header["sequence"]
    stats.last_timestamp = header["timestamp"]
    stats.packet_count += 1
    stats.ssrcs.add(header["ssrc"])
    stats.payload_sizes.add(header["payload_bytes"])


def format_set(values: set[int]) -> str:
    if not values:
        return "-"
    return ",".join(str(value) for value in sorted(values))


def main() -> None:
    args = parse_args()
    plan = load_plan(args.config)

    selector = selectors.DefaultSelector()
    stats_by_id = {stream["id"]: StreamStats(stream=stream) for stream in plan["streams"]}
    sockets: list[socket.socket] = []

    for stream in plan["streams"]:
        sock = open_rtp_socket(args.host, stream["port"], args.iface_ip)
        sockets.append(sock)
        selector.register(sock, selectors.EVENT_READ, stream["id"])

    print("Monitoring all RTP streams")
    print(f"streams:      {plan['stream_count']}")
    print(f"host:         {args.host}")
    print(f"target_count: {args.count}")
    print(f"timeout:      {args.timeout:g}s")
    print()

    deadline = time.monotonic() + args.timeout
    try:
        while time.monotonic() < deadline and not complete(stats_by_id, args.count):
            remaining = max(0.0, deadline - time.monotonic())
            for key, _mask in selector.select(timeout=min(0.2, remaining)):
                stream_id = key.data
                packet, _address = key.fileobj.recvfrom(65535)
                if stats_by_id[stream_id].packet_count >= args.count:
                    continue
                try:
                    header = parse_rtp_header(packet)
                    update_stats(stats_by_id[stream_id], header, plan)
                except ValueError as error:
                    stats_by_id[stream_id].errors.append(str(error))
    finally:
        for sock in sockets:
            selector.unregister(sock)
            sock.close()

    print("stream packets payload_bytes delta_seq delta_ts ssrcs status")
    failures = []

    for stream in plan["streams"]:
        stats = stats_by_id[stream["id"]]
        status = "PASS"
        if stats.packet_count < args.count:
            stats.errors.append(f"packet_count={stats.packet_count}")
        if len(stats.ssrcs) != 1 and stats.packet_count > 0:
            stats.errors.append(f"ssrc_count={len(stats.ssrcs)}")
        if stats.errors:
            status = "FAIL"
            failures.append(stream["name"])

        ssrcs = ",".join(f"0x{ssrc:08x}" for ssrc in sorted(stats.ssrcs)) or "-"
        print(
            f"{stream['name']:9s} "
            f"{stats.packet_count:7d} "
            f"{format_set(stats.payload_sizes):13s} "
            f"{format_set(stats.delta_sequences):9s} "
            f"{format_set(stats.delta_timestamps):8s} "
            f"{ssrcs:20s} "
            f"{status}"
        )

        if stats.errors:
            unique_errors = ", ".join(sorted(set(stats.errors)))
            print(f"  errors: {unique_errors}")

    print()
    if failures:
        print(f"FAILED streams: {', '.join(failures)}")
        raise SystemExit(1)

    print(f"PASS: {len(plan['streams'])} streams reached {args.count} packets")


if __name__ == "__main__":
    main()
