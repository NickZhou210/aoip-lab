#!/usr/bin/env python3
"""Print the most important fields from RTP packets.

This is a learning tool, not a production AES67 receiver.
It joins a multicast group, receives UDP packets, parses the first
12 bytes as an RTP header, and prints the fields you need to recognize.
"""

from __future__ import annotations

import argparse
import ipaddress
import socket
import struct


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect RTP packet headers")
    parser.add_argument("--group", default="239.69.1.1", help="multicast group")
    parser.add_argument("--port", type=int, default=5004, help="UDP/RTP port")
    parser.add_argument("--count", type=int, default=10, help="packets to print")
    parser.add_argument(
        "--iface-ip",
        default="10.211.55.6",
        help="local interface IP used to join the multicast group",
    )
    return parser.parse_args()


def open_rtp_socket(address: str, port: int, iface_ip: str) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
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
        "padding": (first >> 5) & 0x01,
        "extension": (first >> 4) & 0x01,
        "csrc_count": first & 0x0F,
        "marker": second >> 7,
        "payload_type": second & 0x7F,
        "sequence": sequence,
        "timestamp": timestamp,
        "ssrc": ssrc,
        "payload_bytes": len(packet) - 12,
    }


def main() -> None:
    args = parse_args()
    sock = open_rtp_socket(args.group, args.port, args.iface_ip)

    if ipaddress.ip_address(args.group).is_multicast:
        print(f"Listening for multicast RTP on {args.group}:{args.port} via {args.iface_ip}")
    else:
        print(f"Listening for unicast RTP on UDP port {args.port}")
    print("version pt seq delta_seq timestamp delta_ts payload_bytes ssrc")

    last_sequence: int | None = None
    last_timestamp: int | None = None

    for _ in range(args.count):
        packet, address = sock.recvfrom(65535)
        header = parse_rtp_header(packet)

        delta_sequence = "-" if last_sequence is None else (header["sequence"] - last_sequence) % 65536
        delta_timestamp = "-" if last_timestamp is None else (header["timestamp"] - last_timestamp) % (2**32)

        print(
            f"{header['version']} "
            f"{header['payload_type']} "
            f"{header['sequence']} "
            f"{delta_sequence} "
            f"{header['timestamp']} "
            f"{delta_timestamp} "
            f"{header['payload_bytes']} "
            f"0x{header['ssrc']:08x} "
            f"from={address[0]}:{address[1]}"
        )

        last_sequence = header["sequence"]
        last_timestamp = header["timestamp"]


if __name__ == "__main__":
    main()
