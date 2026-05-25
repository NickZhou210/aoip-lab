#!/usr/bin/env python3
"""Model whether multiple RTP streams align to the same PTP playout time."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "project2_rtp_audio_stream" / "config" / "streams.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate multi-stream RTP/PTP alignment")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to streams.json")
    parser.add_argument("--packet-index", type=int, default=0, help="zero-based packet index to inspect")
    parser.add_argument("--rtp-anchor", type=int, default=0, help="RTP timestamp anchor for aligned streams")
    parser.add_argument("--ptp-anchor-ms", type=float, default=0.0, help="PTP time for the RTP anchor")
    parser.add_argument("--playout-latency-ms", type=float, default=50.0, help="receiver playout latency")
    parser.add_argument(
        "--skew-stream",
        type=int,
        help="optional stream id to intentionally offset for demonstration",
    )
    parser.add_argument(
        "--skew-samples",
        type=int,
        default=0,
        help="sample offset added to --skew-stream",
    )
    return parser.parse_args()


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    args = parse_args()
    plan = load_plan(args.config)

    sample_rate = plan["sample_rate_hz"]
    samples_per_packet = plan["samples_per_packet"]
    base_rtp_timestamp = args.rtp_anchor + args.packet_index * samples_per_packet
    media_elapsed_ms = (args.packet_index * samples_per_packet) * 1000 / sample_rate
    aligned_playout_ms = args.ptp_anchor_ms + media_elapsed_ms + args.playout_latency_ms

    print("Multi-stream alignment model")
    print(f"streams:            {plan['stream_count']}")
    print(f"total_channels:     {plan['total_channels']}")
    print(f"sample_rate:        {sample_rate} Hz")
    print(f"samples_per_packet: {samples_per_packet}")
    print(f"packet_index:       {args.packet_index}")
    print(f"rtp_anchor:         {args.rtp_anchor}")
    print(f"ptp_anchor_ms:      {args.ptp_anchor_ms:g}")
    print(f"playout_latency_ms: {args.playout_latency_ms:g}")
    if args.skew_stream is not None and args.skew_samples:
        print(f"intentional_skew:   stream-{args.skew_stream:02d} +{args.skew_samples} samples")
    print()
    print("stream channels rtp_timestamp media_elapsed_ms scheduled_playout_ptp_ms offset_from_stream_01_ms")

    first_playout_ms: float | None = None
    max_offset_ms = 0.0

    for stream in plan["streams"]:
        rtp_timestamp = base_rtp_timestamp
        if args.skew_stream == stream["id"]:
            rtp_timestamp += args.skew_samples

        stream_media_elapsed_ms = (rtp_timestamp - args.rtp_anchor) * 1000 / sample_rate
        scheduled_playout_ms = args.ptp_anchor_ms + stream_media_elapsed_ms + args.playout_latency_ms

        if first_playout_ms is None:
            first_playout_ms = scheduled_playout_ms

        offset_ms = scheduled_playout_ms - first_playout_ms
        max_offset_ms = max(max_offset_ms, abs(offset_ms))

        channels = f"{stream['channel_start']}-{stream['channel_end']}"
        print(
            f"{stream['name']:9s} "
            f"{channels:8s} "
            f"{rtp_timestamp:13d} "
            f"{stream_media_elapsed_ms:16.3f} "
            f"{scheduled_playout_ms:24.3f} "
            f"{offset_ms:24.3f}"
        )

    print()
    print(f"max_alignment_offset_ms: {max_offset_ms:.3f}")
    if max_offset_ms == 0:
        print("alignment_result:        aligned")
    else:
        print("alignment_result:        not aligned")


if __name__ == "__main__":
    main()
