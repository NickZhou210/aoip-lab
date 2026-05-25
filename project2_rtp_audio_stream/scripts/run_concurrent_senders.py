#!/usr/bin/env python3
"""Start all configured RTP senders at the same time."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parents[0]
DEFAULT_CONFIG = PROJECT_DIR / "config" / "streams.json"
DEFAULT_LOG_DIR = PROJECT_DIR / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run configured RTP senders concurrently")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--host", default="127.0.0.1", help="destination host for every sender")
    parser.add_argument(
        "--use-config-groups",
        action="store_true",
        help="send each stream to its multicast group from streams.json instead of --host",
    )
    parser.add_argument("--iface", default="enp0s5", help="multicast interface")
    parser.add_argument("--duration", type=float, default=5.0, help="seconds to run; use 0 to run until Ctrl+C")
    parser.add_argument("--startup-delay", type=float, default=0.05, help="delay between process starts")
    parser.add_argument("--freq-base", type=int, default=1000, help="frequency for stream 1 test tone")
    parser.add_argument("--freq-step", type=int, default=25, help="frequency increment per stream")
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR), help="directory for sender logs")
    return parser.parse_args()


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def stop_process(process: subprocess.Popen, name: str) -> None:
    if process.poll() is not None:
        return

    try:
        os.killpg(process.pid, signal.SIGINT)
        process.wait(timeout=5)
        return
    except ProcessLookupError:
        return
    except subprocess.TimeoutExpired:
        print(f"{name} did not stop after SIGINT; terminating")

    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except ProcessLookupError:
        return
    except subprocess.TimeoutExpired:
        print(f"{name} did not stop after SIGTERM; killing")
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def main() -> None:
    args = parse_args()
    plan = load_plan(args.config)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = Path(args.log_dir) / f"senders-{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    processes: list[tuple[dict, subprocess.Popen, object]] = []

    print("Concurrent RTP sender test")
    print(f"streams:          {plan['stream_count']}")
    print(f"total_channels:   {plan['total_channels']}")
    print(f"host:             {'streams.json groups' if args.use_config_groups else args.host}")
    print(f"duration:         {'until Ctrl+C' if args.duration == 0 else f'{args.duration:g}s'}")
    print(f"log_dir:          {log_dir}")
    print()

    try:
        for stream in plan["streams"]:
            freq = args.freq_base + (stream["id"] - 1) * args.freq_step
            log_path = log_dir / f"{stream['name']}.log"
            log_file = open(log_path, "w", encoding="utf-8")
            command = [
                str(SCRIPT_DIR / "send_stream_from_config.py"),
                "--config",
                args.config,
                "--stream",
                str(stream["id"]),
                "--iface",
                args.iface,
                "--freq",
                str(freq),
            ]
            if not args.use_config_groups:
                command.extend(["--host", args.host])

            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
            processes.append((stream, process, log_file))
            print(
                f"started {stream['name']} "
                f"pid={process.pid} "
                f"dest={(stream['group'] if args.use_config_groups else args.host)}:{stream['port']} "
                f"channels={stream['channel_start']}-{stream['channel_end']} "
                f"freq={freq}"
            )
            time.sleep(args.startup_delay)

        print()
        print(f"started_count: {len(processes)}")

        if args.duration == 0:
            while True:
                time.sleep(1)
                failed = [(stream, process) for stream, process, _log in processes if process.poll() not in (None, 0, 130)]
                if failed:
                    for stream, process in failed:
                        print(f"{stream['name']} exited early with code {process.returncode}")
                    raise SystemExit(1)
        else:
            deadline = time.monotonic() + args.duration
            while time.monotonic() < deadline:
                failed = [(stream, process) for stream, process, _log in processes if process.poll() not in (None, 0, 130)]
                if failed:
                    for stream, process in failed:
                        print(f"{stream['name']} exited early with code {process.returncode}")
                    raise SystemExit(1)
                time.sleep(0.2)
    except KeyboardInterrupt:
        print()
        print("interrupted")
    finally:
        print()
        print("stopping senders")
        for stream, process, _log_file in reversed(processes):
            stop_process(process, stream["name"])

        for _stream, _process, log_file in processes:
            log_file.close()

    failures = []
    for stream, process, _log_file in processes:
        code = process.returncode
        if code not in (0, 130, -signal.SIGINT):
            failures.append(f"{stream['name']}={code}")

    if failures:
        print(f"FAILED sender exit codes: {', '.join(failures)}")
        raise SystemExit(1)

    print(f"PASS: {len(processes)} senders ran concurrently")


if __name__ == "__main__":
    main()
