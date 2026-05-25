#!/usr/bin/env python3
"""Run concurrent RTP senders and sample basic system performance."""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR.parents[0] / "config" / "streams.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure basic performance while 16 RTP senders run")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--host", default="127.0.0.1", help="sender destination host")
    parser.add_argument("--iface", default="lo", help="network interface to sample")
    parser.add_argument("--duration", type=float, default=5.0, help="seconds to sample after startup")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between samples")
    return parser.parse_args()


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def read_cpu() -> tuple[int, int]:
    with open("/proc/stat", "r", encoding="utf-8") as file:
        fields = file.readline().split()

    values = [int(value) for value in fields[1:]]
    idle = values[3] + values[4]
    total = sum(values)
    return total, idle


def cpu_percent(previous: tuple[int, int], current: tuple[int, int]) -> float:
    total_delta = current[0] - previous[0]
    idle_delta = current[1] - previous[1]
    if total_delta <= 0:
        return 0.0
    return (total_delta - idle_delta) * 100 / total_delta


def read_netdev(iface: str) -> tuple[int, int]:
    with open("/proc/net/dev", "r", encoding="utf-8") as file:
        for line in file:
            if ":" not in line:
                continue
            name, data = line.split(":", 1)
            if name.strip() != iface:
                continue
            fields = data.split()
            rx_bytes = int(fields[0])
            tx_bytes = int(fields[8])
            return rx_bytes, tx_bytes
    raise SystemExit(f"network interface {iface!r} was not found")


def process_matches(cmdline: str) -> bool:
    return "gst-launch-1.0" in cmdline or "send_stream_from_config.py" in cmdline


def read_process_rss_kb() -> tuple[int, int]:
    count = 0
    rss_kb = 0
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            cmdline = (path / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", "ignore")
            if not process_matches(cmdline):
                continue
            status = (path / "status").read_text(encoding="utf-8", errors="ignore")
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue

        count += 1
        for line in status.splitlines():
            if line.startswith("VmRSS:"):
                rss_kb += int(line.split()[1])
                break
    return count, rss_kb


def expected_rates(plan: dict) -> tuple[float, float]:
    packets_per_second = 1000 / plan["packet_time_ms"]
    payload_bytes_per_second = sum(stream["payload_bytes"] for stream in plan["streams"]) * packets_per_second
    ip_bytes_per_second = sum(stream["ip_packet_bytes"] for stream in plan["streams"]) * packets_per_second
    return payload_bytes_per_second * 8 / 1_000_000, ip_bytes_per_second * 8 / 1_000_000


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
    plan = load_plan(args.config)
    payload_mbps, ip_mbps = expected_rates(plan)

    sender_cmd = [
        str(SCRIPT_DIR / "run_concurrent_senders.py"),
        "--config",
        args.config,
        "--host",
        args.host,
        "--duration",
        str(args.duration + 3),
    ]

    print("Sender performance probe")
    print(f"streams:                {plan['stream_count']}")
    print(f"total_channels:         {plan['total_channels']}")
    print(f"host:                   {args.host}")
    print(f"sample_iface:           {args.iface}")
    print(f"duration:               {args.duration:g}s")
    print(f"expected_payload_mbps:  {payload_mbps:.3f}")
    print(f"expected_ip_mbps:       {ip_mbps:.3f}")
    print()

    sender = subprocess.Popen(sender_cmd)
    cpu_samples: list[float] = []
    tx_samples: list[float] = []
    rx_samples: list[float] = []
    rss_samples: list[int] = []

    try:
        time.sleep(1.0)
        previous_cpu = read_cpu()
        previous_net = read_netdev(args.iface)
        deadline = time.monotonic() + args.duration

        print("sample cpu_percent tx_mbps rx_mbps sender_processes sender_rss_mib")
        sample = 0
        while time.monotonic() < deadline:
            time.sleep(args.interval)
            current_cpu = read_cpu()
            current_net = read_netdev(args.iface)
            process_count, rss_kb = read_process_rss_kb()

            cpu = cpu_percent(previous_cpu, current_cpu)
            rx_mbps = (current_net[0] - previous_net[0]) * 8 / args.interval / 1_000_000
            tx_mbps = (current_net[1] - previous_net[1]) * 8 / args.interval / 1_000_000
            rss_mib = rss_kb / 1024

            sample += 1
            print(f"{sample:06d} {cpu:11.2f} {tx_mbps:7.3f} {rx_mbps:7.3f} {process_count:16d} {rss_mib:14.1f}")

            cpu_samples.append(cpu)
            tx_samples.append(tx_mbps)
            rx_samples.append(rx_mbps)
            rss_samples.append(rss_kb)

            previous_cpu = current_cpu
            previous_net = current_net
    finally:
        stop_process(sender)

    if sender.returncode not in (0, 130, -signal.SIGINT):
        raise SystemExit(f"sender runner exited with code {sender.returncode}")

    if not cpu_samples:
        raise SystemExit("no samples were collected")

    print()
    print(f"avg_cpu_percent:       {sum(cpu_samples) / len(cpu_samples):.2f}")
    print(f"avg_tx_mbps:           {sum(tx_samples) / len(tx_samples):.3f}")
    print(f"avg_rx_mbps:           {sum(rx_samples) / len(rx_samples):.3f}")
    print(f"peak_sender_rss_mib:   {max(rss_samples) / 1024:.1f}")


if __name__ == "__main__":
    main()
