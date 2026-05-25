#!/usr/bin/env python3
"""Start one RTP sender from streams.json."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "streams.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send one RTP stream from config")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--stream", type=int, required=True, help="stream id to send")
    parser.add_argument(
        "--host",
        help="override destination host; use 127.0.0.1 for local unicast tests",
    )
    parser.add_argument("--iface", default="enp0s5", help="multicast interface")
    parser.add_argument("--freq", type=int, default=1000, help="test tone frequency")
    parser.add_argument("--dry-run", action="store_true", help="print command without running it")
    return parser.parse_args()


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_stream(plan: dict, stream_id: int) -> dict:
    for stream in plan["streams"]:
        if stream["id"] == stream_id:
            return stream
    raise SystemExit(f"stream id {stream_id} was not found")


def ns_from_ms(milliseconds: float) -> int:
    return int(round(milliseconds * 1_000_000))


def build_gst_command(plan: dict, stream: dict, host: str | None, iface: str, freq: int) -> list[str]:
    destination = host or stream["group"]
    ptime_ns = ns_from_ms(plan["packet_time_ms"])
    caps = (
        f"audio/x-raw,format=S16BE,"
        f"rate={plan['sample_rate_hz']},"
        f"channels={stream['channels']}"
    )

    sink = [
        "udpsink",
        f"host={destination}",
        f"port={stream['port']}",
    ]
    if destination != "127.0.0.1":
        sink.extend(
            [
                "auto-multicast=true",
                f"multicast-iface={iface}",
                "loop=true",
                "ttl-mc=16",
            ]
        )

    return [
        "gst-launch-1.0",
        "audiotestsrc",
        "wave=sine",
        f"freq={freq}",
        "is-live=true",
        "!",
        caps,
        "!",
        "rtpL16pay",
        f"pt={stream['payload_type']}",
        f"min-ptime={ptime_ns}",
        f"max-ptime={ptime_ns}",
        f"ptime-multiple={ptime_ns}",
        "mtu=1200",
        "!",
        *sink,
    ]


def main() -> None:
    args = parse_args()
    plan = load_plan(args.config)
    stream = find_stream(plan, args.stream)
    command = build_gst_command(plan, stream, args.host, args.iface, args.freq)

    destination = args.host or stream["group"]
    print(f"Starting {stream['name']}")
    print(f"Destination: {destination}:{stream['port']}")
    print(f"Channels: {stream['channel_start']}-{stream['channel_end']} ({stream['channels']}ch)")
    print(f"Format: {plan['encoding']}/{plan['sample_rate_hz']}")
    print(f"Packet time: {plan['packet_time_ms']} ms")
    print(f"Expected payload bytes: {stream['payload_bytes']}")
    print()
    print("Command:")
    print(" ".join(command))

    if args.dry_run:
        return

    try:
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(130)


if __name__ == "__main__":
    main()
