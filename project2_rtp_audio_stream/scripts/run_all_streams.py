#!/usr/bin/env python3
"""Run loopback tests for every configured RTP stream."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR.parents[0] / "config" / "streams.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all configured RTP loopback tests")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--duration", type=float, default=1.5, help="sender run duration per stream")
    parser.add_argument("--host", default="127.0.0.1", help="sender destination host")
    parser.add_argument("--stop-on-fail", action="store_true", help="stop after the first failed stream")
    return parser.parse_args()


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    args = parse_args()
    plan = load_plan(args.config)
    failures = []

    for stream in plan["streams"]:
        print("=" * 72)
        print(f"Testing {stream['name']} ({stream['channel_start']}-{stream['channel_end']})")
        command = [
            str(SCRIPT_DIR / "run_stream_pair.py"),
            "--config",
            args.config,
            "--stream",
            str(stream["id"]),
            "--duration",
            str(args.duration),
            "--host",
            args.host,
        ]
        result = subprocess.run(command)
        if result.returncode != 0:
            failures.append(stream["name"])
            print(f"FAIL: {stream['name']}")
            if args.stop_on_fail:
                break

    print("=" * 72)
    if failures:
        print(f"FAILED streams: {', '.join(failures)}")
        raise SystemExit(1)

    print(f"PASS: {len(plan['streams'])} streams")


if __name__ == "__main__":
    main()

