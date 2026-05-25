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
    return parser.parse_args()


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def sdp_for_stream(plan: dict, stream: dict, origin_ip: str, direction: str) -> str:
    payload_type = stream["payload_type"]
    packet_time = int(plan["packet_time_ms"])
    session_name = (
        f"AOIP Lab {stream['name']} "
        f"ch{stream['channel_start']}-{stream['channel_end']}"
    )

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
        sdp = sdp_for_stream(plan, stream, args.origin_ip, args.direction)
        output_path = output_dir / f"{stream['name']}.sdp"
        output_path.write_text(sdp, encoding="utf-8")
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()

