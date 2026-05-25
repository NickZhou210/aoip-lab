#!/usr/bin/env python3
"""Receive one RTP stream from streams.json and write a WAV file."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "streams.json"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "receiver"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Receive one RTP stream from config")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--stream", type=int, required=True, help="stream id to receive")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="directory for WAV output")
    parser.add_argument("--output", help="override WAV output path")
    parser.add_argument("--latency-ms", type=int, default=50, help="RTP jitter buffer latency")
    parser.add_argument("--no-jitterbuffer", action="store_true", help="depay RTP without jitter buffering")
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


def build_gst_command(
    plan: dict,
    stream: dict,
    output: Path,
    latency_ms: int,
    use_jitterbuffer: bool,
) -> list[str]:
    caps = (
        "application/x-rtp,"
        "media=audio,"
        f"encoding-name={plan['encoding']},"
        f"clock-rate={plan['sample_rate_hz']},"
        f"channels={stream['channels']},"
        f"payload={stream['payload_type']}"
    )

    command = [
        "gst-launch-1.0",
        "-e",
        "udpsrc",
        f"port={stream['port']}",
        f"caps={caps}",
        "!",
    ]

    if use_jitterbuffer:
        command.extend(["rtpjitterbuffer", f"latency={latency_ms}", "!"])

    command.extend(
        [
            "rtpL16depay",
            "!",
            "audioconvert",
            "!",
            "wavenc",
            "!",
            "filesink",
            f"location={output}",
        ]
    )
    return command


def main() -> None:
    args = parse_args()
    plan = load_plan(args.config)
    stream = find_stream(plan, args.stream)

    output = Path(args.output) if args.output else Path(args.output_dir) / f"{stream['name']}.wav"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = build_gst_command(
        plan,
        stream,
        output,
        args.latency_ms,
        use_jitterbuffer=not args.no_jitterbuffer,
    )

    print(f"Receiving {stream['name']}")
    print(f"Port: {stream['port']}")
    print(f"Channels: {stream['channel_start']}-{stream['channel_end']} ({stream['channels']}ch)")
    print(f"Format: {plan['encoding']}/{plan['sample_rate_hz']}")
    print(f"Payload type: {stream['payload_type']}")
    print(f"Jitter buffer: {'off' if args.no_jitterbuffer else 'on'}")
    print(f"Output: {output}")
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
