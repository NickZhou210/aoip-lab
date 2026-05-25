#!/usr/bin/env python3
"""Summarize the learning ptp4l configuration files."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"
KEYS = [
    "domainNumber",
    "priority1",
    "priority2",
    "clockClass",
    "clockAccuracy",
    "offsetScaledLogVariance",
    "clientOnly",
    "free_running",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize ptp4l learning configs")
    parser.add_argument("--config-dir", default=str(DEFAULT_CONFIG_DIR), help="directory containing ptp4l cfg files")
    return parser.parse_args()


def parse_config(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            values[parts[0]] = parts[1].strip()
    return values


def main() -> None:
    args = parse_args()
    config_dir = Path(args.config_dir)
    paths = sorted(config_dir.glob("*.cfg"))

    print("PTP config summary")
    print(f"config_dir: {config_dir}")
    print()
    print("config                         " + " ".join(f"{key:>24s}" for key in KEYS))

    for path in paths:
        values = parse_config(path)
        row = [path.name.ljust(30)]
        for key in KEYS:
            row.append(f"{values.get(key, '-'):>24s}")
        print(" ".join(row))

    print()
    print("Interpretation")
    print("priority1/priority2: lower values are preferred by BMCA")
    print("domainNumber: clocks in different domains do not elect each other")
    print("clientOnly=1: this node should not become Grandmaster")
    print("free_running=1: observe behavior without adjusting the local clock")


if __name__ == "__main__":
    main()
