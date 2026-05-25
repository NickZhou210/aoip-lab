#!/usr/bin/env python3
"""Generate SDP files from streams.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "streams.json"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "sdp" / "generated"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SDP files for configured RTP streams")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="directory for SDP files")
    parser.add_argument("--origin-ip", default="10.211.55.6", help="IP address for the SDP origin line")
    parser.add_argument("--direction", default="recvonly", choices=("recvonly", "sendonly"), help="SDP media direction")
    parser.add_argument(
        "--ptp-grandmaster",
        help="optional PTP grandmaster clock identity, for example 00-1C-42-FF-FE-EE-3F-40",
    )
    parser.add_argument("--ptp-domain", type=int, default=0, help="PTP domain used in ts-refclk")
    parser.add_argument(
        "--mediaclk-direct",
        default="0",
        help="RTP media clock direct offset used when --ptp-grandmaster is set",
    )
    return parser.parse_args()


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_clock_identity(clock_identity: str) -> str:
    hex_digits = "".join(character for character in clock_identity if character.isalnum())
    if len(hex_digits) != 16 or not all(character in "0123456789abcdefABCDEF" for character in hex_digits):
        raise SystemExit(
            "PTP grandmaster clock identity must contain 16 hex digits, "
            "for example 00-1C-42-FF-FE-EE-3F-40"
        )
    pairs = [hex_digits[index : index + 2].upper() for index in range(0, 16, 2)]
    return "-".join(pairs)


def sdp_for_stream(
    plan: dict,
    stream: dict,
    origin_ip: str,
    direction: str,
    ptp_grandmaster: str | None,
    ptp_domain: int,
    mediaclk_direct: str,
) -> str:
    payload_type = stream["payload_type"]
    packet_time = int(plan["packet_time_ms"])
    session_name = (
        f"AOIP Lab {stream['name']} "
        f"ch{stream['channel_start']}-{stream['channel_end']}"
    )
    clock_lines = []
    if ptp_grandmaster:
        grandmaster = normalize_clock_identity(ptp_grandmaster)
        clock_lines = [
            f"a=ts-refclk:ptp=IEEE1588-2008:{grandmaster}:{ptp_domain}",
            f"a=mediaclk:direct={mediaclk_direct}",
        ]

    return "\n".join(
        [
            "v=0",
            f"o=- {stream['id']} 1 IN IP4 {origin_ip}",
            f"s={session_name}",
            f"c=IN IP4 {stream['group']}/32",
            "t=0 0",
            f"m=audio {stream['port']} RTP/AVP {payload_type}",
            f"a=rtpmap:{payload_type} {plan['encoding']}/{plan['sample_rate_hz']}/{stream['channels']}",
            f"a=ptime:{packet_time}",
            f"a={direction}",
            *clock_lines,
            f"a=x-aoip-channel-range:{stream['channel_start']}-{stream['channel_end']}",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    plan = load_plan(args.config)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for stream in plan["streams"]:
        sdp = sdp_for_stream(
            plan,
            stream,
            args.origin_ip,
            args.direction,
            args.ptp_grandmaster,
            args.ptp_domain,
            args.mediaclk_direct,
        )
        output_path = output_dir / f"{stream['name']}.sdp"
        output_path.write_text(sdp, encoding="utf-8")
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
