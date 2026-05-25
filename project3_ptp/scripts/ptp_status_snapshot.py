#!/usr/bin/env python3
"""Collect a concise status snapshot from a running ptp4l instance."""

from __future__ import annotations

import argparse
import re
import subprocess
from shutil import which


COMMANDS = {
    "PORT_DATA_SET": "GET PORT_DATA_SET",
    "CURRENT_DATA_SET": "GET CURRENT_DATA_SET",
    "PARENT_DATA_SET": "GET PARENT_DATA_SET",
    "TIME_STATUS_NP": "GET TIME_STATUS_NP",
}

FIELDS = {
    "portIdentity",
    "portState",
    "stepsRemoved",
    "offsetFromMaster",
    "meanPathDelay",
    "parentPortIdentity",
    "grandmasterPriority1",
    "gm.ClockClass",
    "gm.ClockAccuracy",
    "gm.OffsetScaledLogVariance",
    "grandmasterPriority2",
    "grandmasterIdentity",
    "master_offset",
    "ingress_time",
    "cumulativeScaledRateOffset",
    "gmPresent",
    "gmIdentity",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture concise ptp4l/pmc status")
    parser.add_argument("--domain", type=int, default=0, help="PTP domain number for pmc")
    parser.add_argument("--no-sudo", action="store_true", help="do not use sudo for pmc")
    parser.add_argument("--raw", action="store_true", help="also print raw pmc output")
    return parser.parse_args()


def run_text(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, text=True, capture_output=True)
    output = result.stdout
    if result.stderr:
        output += result.stderr
    return result.returncode, output


def command_prefix(no_sudo: bool) -> list[str]:
    if no_sudo or which("sudo") is None:
        return ["pmc"]
    if subprocess.run(["id", "-u"], text=True, capture_output=True).stdout.strip() == "0":
        return ["pmc"]
    return ["sudo", "pmc"]


def parse_fields(output: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in output.splitlines():
        stripped = line.strip()
        for field in FIELDS:
            if stripped.startswith(field):
                value = re.sub(rf"^{re.escape(field)}\s+", "", stripped)
                parsed[field] = value
    return parsed


def pgrep_ptp4l() -> str:
    code, output = run_text(["pgrep", "-af", "ptp4l"])
    if code != 0:
        return "not running"
    lines = [line for line in output.splitlines() if "pgrep -af ptp4l" not in line]
    return "\n".join(lines) if lines else "not running"


def main() -> None:
    args = parse_args()
    prefix = command_prefix(args.no_sudo)

    print("PTP status snapshot")
    print(f"domain: {args.domain}")
    print()
    print("== ptp4l process ==")
    process_status = pgrep_ptp4l()
    print(process_status)
    print()

    if process_status == "not running":
        print("ptp4l is not running. Start ptp4l first, then run this snapshot command again.")
        raise SystemExit(1)

    all_fields: dict[str, dict[str, str]] = {}
    failures: list[str] = []

    for name, pmc_command in COMMANDS.items():
        command = [*prefix, "-u", "-b", "0", "-d", str(args.domain), pmc_command]
        code, output = run_text(command)
        if args.raw:
            print(f"== raw {name} ==")
            print(output.rstrip())
            print()
        if code != 0:
            failures.append(name)
            all_fields[name] = {"error": output.strip() or f"pmc exited with {code}"}
        else:
            all_fields[name] = parse_fields(output)

    print("== summary ==")
    summary_order = [
        ("PORT_DATA_SET", "portIdentity"),
        ("PORT_DATA_SET", "portState"),
        ("CURRENT_DATA_SET", "stepsRemoved"),
        ("CURRENT_DATA_SET", "offsetFromMaster"),
        ("CURRENT_DATA_SET", "meanPathDelay"),
        ("PARENT_DATA_SET", "parentPortIdentity"),
        ("PARENT_DATA_SET", "grandmasterPriority1"),
        ("PARENT_DATA_SET", "gm.ClockClass"),
        ("PARENT_DATA_SET", "gm.ClockAccuracy"),
        ("PARENT_DATA_SET", "gm.OffsetScaledLogVariance"),
        ("PARENT_DATA_SET", "grandmasterPriority2"),
        ("PARENT_DATA_SET", "grandmasterIdentity"),
        ("TIME_STATUS_NP", "master_offset"),
        ("TIME_STATUS_NP", "cumulativeScaledRateOffset"),
        ("TIME_STATUS_NP", "gmPresent"),
        ("TIME_STATUS_NP", "gmIdentity"),
    ]

    for section, field in summary_order:
        value = all_fields.get(section, {}).get(field, "-")
        print(f"{field:30s} {value}")

    for section, fields in all_fields.items():
        if "error" in fields:
            print(f"{section:30s} ERROR: {fields['error']}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
