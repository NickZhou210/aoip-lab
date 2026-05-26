#!/usr/bin/env python3
"""Validate generated SDP files for configured AES67-style RTP streams."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parents[0]
DEFAULT_CONFIG = PROJECT_DIR / "config" / "streams.json"
DEFAULT_SDP_DIR = PROJECT_DIR / "sdp" / "generated-ptp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated SDP clock reference lines")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--sdp-dir", default=str(DEFAULT_SDP_DIR), help="directory containing SDP files")
    parser.add_argument(
        "--ptp-grandmaster",
        default="00-1C-42-FF-FE-EE-3F-40",
        help="expected PTP grandmaster clock identity",
    )
    parser.add_argument("--ptp-domain", type=int, default=0, help="expected PTP domain")
    parser.add_argument("--mediaclk-direct", default="0", help="expected mediaclk direct value")
    return parser.parse_args()


def load_plan(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_clock_identity(clock_identity: str) -> str:
    hex_digits = "".join(character for character in clock_identity if character.isalnum())
    if len(hex_digits) != 16 or not all(character in "0123456789abcdefABCDEF" for character in hex_digits):
        raise SystemExit("PTP grandmaster clock identity must contain 16 hex digits")
    return "-".join(hex_digits[index : index + 2].upper() for index in range(0, 16, 2))


def require_line(lines: set[str], expected: str, path: Path) -> None:
    if expected not in lines:
        raise SystemExit(f"{path}: missing expected SDP line: {expected}")


def main() -> None:
    args = parse_args()
    plan = load_plan(Path(args.config))
    sdp_dir = Path(args.sdp_dir)
    grandmaster = normalize_clock_identity(args.ptp_grandmaster)
    expected_ts_refclk = f"a=ts-refclk:ptp=IEEE1588-2008:{grandmaster}:{args.ptp_domain}"
    expected_mediaclk = f"a=mediaclk:direct={args.mediaclk_direct}"

    print("SDP clock reference validation")
    print(f"sdp_dir:          {sdp_dir}")
    print(f"streams:          {plan['stream_count']}")
    print(f"ptp_grandmaster:  {grandmaster}")
    print(f"ptp_domain:       {args.ptp_domain}")
    print(f"mediaclk_direct:  {args.mediaclk_direct}")
    print()
    print("stream file          group          port clock_lines status")

    passed = 0
    for stream in plan["streams"]:
        path = sdp_dir / f"{stream['name']}.sdp"
        if not path.exists():
            raise SystemExit(f"missing SDP file: {path}")

        lines = set(path.read_text(encoding="utf-8").splitlines())
        require_line(lines, f"c=IN IP4 {stream['group']}/32", path)
        require_line(lines, f"m=audio {stream['port']} RTP/AVP {stream['payload_type']}", path)
        require_line(
            lines,
            f"a=rtpmap:{stream['payload_type']} {plan['encoding']}/{plan['sample_rate_hz']}/{stream['channels']}",
            path,
        )
        require_line(lines, f"a=ptime:{int(plan['packet_time_ms'])}", path)
        require_line(lines, expected_ts_refclk, path)
        require_line(lines, expected_mediaclk, path)

        passed += 1
        print(
            f"{stream['name']:9} "
            f"{path.name:13} "
            f"{stream['group']:14} "
            f"{stream['port']:<5} "
            f"ts-refclk,mediaclk PASS"
        )

    print()
    print(f"PASS: {passed} SDP files contain expected RTP and PTP clock reference lines")


if __name__ == "__main__":
    main()
