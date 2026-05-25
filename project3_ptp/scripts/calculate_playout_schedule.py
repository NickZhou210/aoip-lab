#!/usr/bin/env python3
"""Show how a receiver maps RTP timestamp to scheduled playback time."""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate RTP receiver playout schedule")
    parser.add_argument("--sample-rate", type=int, default=48000, help="RTP audio clock rate")
    parser.add_argument("--packet-time-ms", type=float, default=1.0, help="audio duration per RTP packet")
    parser.add_argument("--count", type=int, default=10, help="number of packets to show")
    parser.add_argument("--rtp-anchor", type=int, default=0, help="RTP timestamp used as the timeline anchor")
    parser.add_argument(
        "--ptp-anchor-ms",
        type=float,
        default=0.0,
        help="PTP time, in milliseconds, that corresponds to --rtp-anchor",
    )
    parser.add_argument(
        "--playout-latency-ms",
        type=float,
        default=50.0,
        help="receiver buffer/playout latency added after the PTP anchor",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    samples_per_packet = round(args.sample_rate * args.packet_time_ms / 1000)

    print("Receiver playout schedule model")
    print(f"sample_rate:        {args.sample_rate} Hz")
    print(f"packet_time:        {args.packet_time_ms:g} ms")
    print(f"samples_per_packet: {samples_per_packet}")
    print(f"rtp_anchor:         {args.rtp_anchor}")
    print(f"ptp_anchor_ms:      {args.ptp_anchor_ms:g}")
    print(f"playout_latency_ms: {args.playout_latency_ms:g}")
    print()
    print("packet rtp_timestamp media_elapsed_ms scheduled_playout_ptp_ms")

    for packet_index in range(args.count):
        rtp_timestamp = (args.rtp_anchor + packet_index * samples_per_packet) % (2**32)
        media_elapsed_ms = packet_index * samples_per_packet * 1000 / args.sample_rate
        scheduled_playout_ptp_ms = args.ptp_anchor_ms + media_elapsed_ms + args.playout_latency_ms

        print(
            f"{packet_index + 1:06d} "
            f"{rtp_timestamp:13d} "
            f"{media_elapsed_ms:16.3f} "
            f"{scheduled_playout_ptp_ms:24.3f}"
        )


if __name__ == "__main__":
    main()
