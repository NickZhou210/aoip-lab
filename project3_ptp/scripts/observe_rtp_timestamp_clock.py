#!/usr/bin/env python3
"""Compare RTP timestamp progress with local packet arrival time.

This is a learning tool for the bridge between RTP and PTP.
It does not synchronize to PTP yet. It shows that RTP timestamps are a media
clock: at 48 kHz, 48 timestamp ticks means 1 ms of audio time.
"""

from __future__ import annotations

import argparse
import ipaddress
import socket
import struct
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Observe RTP timestamp clock progress")
    parser.add_argument("--group", default="127.0.0.1", help="unicast address or multicast group")
    parser.add_argument("--port", type=int, default=5004, help="UDP/RTP port")
    parser.add_argument("--count", type=int, default=20, help="packets to observe")
    parser.add_argument("--sample-rate", type=int, default=48000, help="RTP audio clock rate")
    parser.add_argument(
        "--iface-ip",
        default="10.211.55.6",
        help="local interface IP used to join a multicast group",
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
        "payload_type": second & 0x7F,
        "sequence": sequence,
        "timestamp": timestamp,
        "ssrc": ssrc,
        "payload_bytes": len(packet) - 12,
    }


def rtp_delta(newer: int, older: int) -> int:
    return (newer - older) % (2**32)


def main() -> None:
    args = parse_args()
    sock = open_rtp_socket(args.group, args.port, args.iface_ip)

    print(f"Listening for RTP on {args.group}:{args.port}")
    print(f"Sample rate: {args.sample_rate} Hz")
    print()
    print(
        "idx seq delta_ts rtp_elapsed_ms arrival_elapsed_ms "
        "arrival_minus_rtp_ms payload_bytes"
    )

    first_timestamp: int | None = None
    first_arrival: float | None = None
    last_timestamp: int | None = None

    for index in range(1, args.count + 1):
        packet, _address = sock.recvfrom(65535)
        arrival = time.monotonic()
        header = parse_rtp_header(packet)

        if first_timestamp is None:
            first_timestamp = header["timestamp"]
            first_arrival = arrival

        delta_ts = 0 if last_timestamp is None else rtp_delta(header["timestamp"], last_timestamp)
        rtp_elapsed_ticks = rtp_delta(header["timestamp"], first_timestamp)
        rtp_elapsed_ms = rtp_elapsed_ticks * 1000 / args.sample_rate
        arrival_elapsed_ms = (arrival - first_arrival) * 1000
        arrival_minus_rtp_ms = arrival_elapsed_ms - rtp_elapsed_ms

        print(
            f"{index:03d} "
            f"{header['sequence']:5d} "
            f"{delta_ts:8d} "
            f"{rtp_elapsed_ms:14.3f} "
            f"{arrival_elapsed_ms:18.3f} "
            f"{arrival_minus_rtp_ms:20.3f} "
            f"{header['payload_bytes']:5d}"
        )

        last_timestamp = header["timestamp"]


if __name__ == "__main__":
    main()
