#!/usr/bin/env python3
"""Run 16 senders and monitor all RTP streams."""

from __future__ import annotations

import argparse
import signal
import subprocess
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR.parents[0] / "config" / "streams.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run concurrent senders and monitor RTP headers")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--host", default="127.0.0.1", help="sender destination and monitor bind address")
    parser.add_argument(
        "--use-config-groups",
        action="store_true",
        help="send and monitor each stream using multicast groups from streams.json",
    )
    parser.add_argument("--iface", default="enp0s5", help="sender multicast interface")
    parser.add_argument("--iface-ip", default="10.211.55.6", help="local interface IP for multicast joins")
    parser.add_argument("--count", type=int, default=20, help="packets to monitor per stream")
    parser.add_argument("--sender-duration", type=float, default=6.0, help="maximum sender runtime")
    parser.add_argument("--monitor-timeout", type=float, default=5.0, help="monitor timeout")
    return parser.parse_args()


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=5)


def main() -> None:
    args = parse_args()

    sender_cmd = [
        str(SCRIPT_DIR / "run_concurrent_senders.py"),
        "--config",
        args.config,
        "--host",
        args.host,
        "--duration",
        str(args.sender_duration),
        "--iface",
        args.iface,
    ]
    if args.use_config_groups:
        sender_cmd.append("--use-config-groups")

    monitor_cmd = [
        str(SCRIPT_DIR / "monitor_all_streams.py"),
        "--config",
        args.config,
        "--host",
        args.host,
        "--count",
        str(args.count),
        "--timeout",
        str(args.monitor_timeout),
        "--iface-ip",
        args.iface_ip,
    ]
    if args.use_config_groups:
        monitor_cmd.append("--use-config-groups")

    print("Starting concurrent senders")
    sender = subprocess.Popen(sender_cmd)
    try:
        time.sleep(1.0)
        print()
        print("Starting all-stream RTP monitor")
        result = subprocess.run(monitor_cmd)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    finally:
        stop_process(sender)

    if sender.returncode not in (0, 130, -signal.SIGINT):
        raise SystemExit(f"sender runner exited with code {sender.returncode}")


if __name__ == "__main__":
    main()
