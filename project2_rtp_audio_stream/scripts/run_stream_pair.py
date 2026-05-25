#!/usr/bin/env python3
"""Run a local sender/receiver loopback test for one configured stream."""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR.parents[0] / "config" / "streams.json"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parents[0] / "receiver"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one config-driven RTP loopback test")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--stream", type=int, required=True, help="stream id to test")
    parser.add_argument("--duration", type=float, default=3.0, help="sender run duration in seconds")
    parser.add_argument("--host", default="127.0.0.1", help="sender destination host")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="directory for WAV output")
    return parser.parse_args()


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_stream(plan: dict, stream_id: int) -> dict:
    for stream in plan["streams"]:
        if stream["id"] == stream_id:
            return stream
    raise SystemExit(f"stream id {stream_id} was not found")


def stop_process(process: subprocess.Popen, name: str) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print(f"{name} did not stop after SIGINT; terminating")
        process.terminate()
        process.wait(timeout=5)


def main() -> None:
    args = parse_args()
    plan = load_plan(args.config)
    stream = find_stream(plan, args.stream)
    output_path = Path(args.output_dir) / f"{stream['name']}.wav"

    if output_path.exists():
        output_path.unlink()

    receiver_cmd = [
        str(SCRIPT_DIR / "receive_stream_from_config.py"),
        "--config",
        args.config,
        "--stream",
        str(args.stream),
        "--output",
        str(output_path),
        "--no-jitterbuffer",
    ]
    sender_cmd = [
        str(SCRIPT_DIR / "send_stream_from_config.py"),
        "--config",
        args.config,
        "--stream",
        str(args.stream),
        "--host",
        args.host,
    ]

    print(f"Testing {stream['name']} for {args.duration:g}s")
    print(f"Expected channels: {stream['channels']}")
    print(f"Expected payload bytes: {stream['payload_bytes']}")
    print(f"Output: {output_path}")

    receiver = subprocess.Popen(receiver_cmd)
    time.sleep(1)
    sender = subprocess.Popen(sender_cmd)

    try:
        time.sleep(args.duration)
    finally:
        stop_process(sender, "sender")
        stop_process(receiver, "receiver")

    if not output_path.exists():
        raise SystemExit("FAIL: output WAV was not created")

    size = output_path.stat().st_size
    print(f"WAV size: {size} bytes")
    if size <= 80:
        raise SystemExit("FAIL: output WAV only contains a header")

    file_result = subprocess.run(["file", str(output_path)], check=True, text=True, capture_output=True)
    print(file_result.stdout.strip())

    expected_fragments = [f"{stream['channels']} channels", f"{plan['sample_rate_hz']} Hz"]
    missing = [fragment for fragment in expected_fragments if fragment not in file_result.stdout]
    if missing:
        raise SystemExit(f"FAIL: file output missing expected text: {', '.join(missing)}")

    print("PASS")


if __name__ == "__main__":
    main()

