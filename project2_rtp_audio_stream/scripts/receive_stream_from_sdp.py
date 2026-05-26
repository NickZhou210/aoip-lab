#!/usr/bin/env python3
"""Receive one RTP stream using only an SDP file."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "receiver"


@dataclass
class SdpStream:
    session_name: str
    group: str
    port: int
    payload_type: int
    encoding: str
    sample_rate: int
    channels: int
    packet_time_ms: float
    direction: str | None
    ts_refclk: str | None
    mediaclk: str | None
    channel_range: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Receive one RTP stream from an SDP file")
    parser.add_argument("sdp", help="path to one SDP file")
    parser.add_argument("--iface", default="enp0s5", help="multicast interface")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="directory for WAV output")
    parser.add_argument("--output", help="override WAV output path")
    parser.add_argument("--latency-ms", type=int, default=50, help="RTP jitter buffer latency")
    parser.add_argument("--no-jitterbuffer", action="store_true", help="depay RTP without jitter buffering")
    parser.add_argument("--dry-run", action="store_true", help="print command without running it")
    return parser.parse_args()


def parse_sdp(path: Path) -> SdpStream:
    session_name = path.stem
    group: str | None = None
    port: int | None = None
    media_payload_type: int | None = None
    rtpmap_payload_type: int | None = None
    encoding: str | None = None
    sample_rate: int | None = None
    channels: int | None = None
    packet_time_ms: float | None = None
    direction: str | None = None
    ts_refclk: str | None = None
    mediaclk: str | None = None
    channel_range: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("s="):
            session_name = line[2:]
        elif line.startswith("c=IN IP4 "):
            group = line.removeprefix("c=IN IP4 ").split("/")[0]
        elif line.startswith("m=audio "):
            parts = line.split()
            if len(parts) < 4:
                raise SystemExit(f"{path}: invalid media line: {line}")
            port = int(parts[1])
            media_payload_type = int(parts[3])
        elif line.startswith("a=rtpmap:"):
            match = re.fullmatch(r"a=rtpmap:(\d+) ([^/]+)/(\d+)/(\d+)", line)
            if not match:
                raise SystemExit(f"{path}: unsupported rtpmap line: {line}")
            rtpmap_payload_type = int(match.group(1))
            encoding = match.group(2)
            sample_rate = int(match.group(3))
            channels = int(match.group(4))
        elif line.startswith("a=ptime:"):
            packet_time_ms = float(line.removeprefix("a=ptime:"))
        elif line in ("a=sendonly", "a=recvonly", "a=sendrecv", "a=inactive"):
            direction = line.removeprefix("a=")
        elif line.startswith("a=ts-refclk:"):
            ts_refclk = line
        elif line.startswith("a=mediaclk:"):
            mediaclk = line
        elif line.startswith("a=x-aoip-channel-range:"):
            channel_range = line.removeprefix("a=x-aoip-channel-range:")

    missing = [
        name
        for name, value in [
            ("c=IN IP4", group),
            ("m=audio", port),
            ("m=audio payload type", media_payload_type),
            ("a=rtpmap", rtpmap_payload_type),
            ("a=rtpmap encoding", encoding),
            ("a=rtpmap sample rate", sample_rate),
            ("a=rtpmap channels", channels),
            ("a=ptime", packet_time_ms),
        ]
        if value is None
    ]
    if missing:
        raise SystemExit(f"{path}: missing required SDP fields: {', '.join(missing)}")
    if media_payload_type != rtpmap_payload_type:
        raise SystemExit(
            f"{path}: media payload type {media_payload_type} does not match rtpmap {rtpmap_payload_type}"
        )

    return SdpStream(
        session_name=session_name,
        group=group,
        port=port,
        payload_type=media_payload_type,
        encoding=encoding,
        sample_rate=sample_rate,
        channels=channels,
        packet_time_ms=packet_time_ms,
        direction=direction,
        ts_refclk=ts_refclk,
        mediaclk=mediaclk,
        channel_range=channel_range,
    )


def build_gst_command(
    stream: SdpStream,
    output: Path,
    iface: str,
    latency_ms: int,
    use_jitterbuffer: bool,
) -> list[str]:
    caps = (
        "application/x-rtp,"
        "media=audio,"
        f"encoding-name={stream.encoding},"
        f"clock-rate={stream.sample_rate},"
        f"channels={stream.channels},"
        f"payload={stream.payload_type}"
    )

    command = [
        "gst-launch-1.0",
        "-e",
        "udpsrc",
        f"multicast-group={stream.group}",
        f"multicast-iface={iface}",
        "auto-multicast=true",
        f"port={stream.port}",
        f"caps={caps}",
        "!",
    ]

    if use_jitterbuffer:
        command.extend(["rtpjitterbuffer", f"latency={latency_ms}", "!"])

    command.extend(
        [
            "rtpL16depay",
            "!",
            "audioconvert",
            "!",
            "wavenc",
            "!",
            "filesink",
            f"location={output}",
        ]
    )
    return command


def main() -> None:
    args = parse_args()
    sdp_path = Path(args.sdp)
    stream = parse_sdp(sdp_path)

    output = Path(args.output) if args.output else Path(args.output_dir) / f"{sdp_path.stem}.wav"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = build_gst_command(
        stream,
        output,
        args.iface,
        args.latency_ms,
        use_jitterbuffer=not args.no_jitterbuffer,
    )

    print("Receiving RTP stream from SDP")
    print(f"SDP:           {sdp_path}")
    print(f"Session:       {stream.session_name}")
    print(f"Group:         {stream.group}")
    print(f"Port:          {stream.port}")
    print(f"Format:        {stream.encoding}/{stream.sample_rate}/{stream.channels}")
    print(f"Payload type:  {stream.payload_type}")
    print(f"Packet time:   {stream.packet_time_ms:g} ms")
    print(f"Direction:     {stream.direction or 'not specified'}")
    print(f"Channel range: {stream.channel_range or 'not specified'}")
    print(f"ts-refclk:     {stream.ts_refclk or 'not specified'}")
    print(f"mediaclk:      {stream.mediaclk or 'not specified'}")
    print(f"Jitter buffer: {'off' if args.no_jitterbuffer else 'on'}")
    print(f"Output:        {output}")
    print()
    print("Command:")
    print(" ".join(command))

    if args.dry_run:
        return

    try:
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(130)


if __name__ == "__main__":
    main()
