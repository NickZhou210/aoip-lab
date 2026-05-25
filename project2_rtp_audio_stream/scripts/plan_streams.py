#!/usr/bin/env python3
"""Plan how to split a large audio channel count into RTP streams."""

from __future__ import annotations

import argparse
import json
import math


RTP_UDP_IPV4_HEADER_BYTES = 12 + 8 + 20
DEFAULT_MTU_BYTES = 1500


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan RTP stream splitting")
    parser.add_argument("--total-channels", type=int, default=128, help="total audio channels")
    parser.add_argument("--channels-per-stream", type=int, default=8, help="channels in each RTP stream")
    parser.add_argument("--rate", type=int, default=48000, help="sample rate in Hz")
    parser.add_argument("--bits", type=int, default=16, choices=(16, 24), help="bits per sample")
    parser.add_argument("--ptime-ms", type=float, default=1.0, help="packet time in milliseconds")
    parser.add_argument("--base-port", type=int, default=5004, help="first UDP/RTP port")
    parser.add_argument("--port-step", type=int, default=2, help="port increment per stream")
    parser.add_argument("--base-group", default="239.69.1.", help="multicast group prefix")
    parser.add_argument("--base-group-index", type=int, default=1, help="first multicast group suffix")
    parser.add_argument("--mtu", type=int, default=DEFAULT_MTU_BYTES, help="IP MTU bytes")
    parser.add_argument("--json-out", help="write the stream plan to this JSON file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    bytes_per_sample = args.bits // 8
    samples_per_packet = round(args.rate * args.ptime_ms / 1000)
    max_payload = args.mtu - RTP_UDP_IPV4_HEADER_BYTES
    stream_count = math.ceil(args.total_channels / args.channels_per_stream)

    streams = []
    for index in range(stream_count):
        first_channel = index * args.channels_per_stream + 1
        last_channel = min((index + 1) * args.channels_per_stream, args.total_channels)
        channels = last_channel - first_channel + 1
        payload = samples_per_packet * bytes_per_sample * channels
        ip_packet = payload + RTP_UDP_IPV4_HEADER_BYTES
        group = f"{args.base_group}{args.base_group_index + index}"
        port = args.base_port + index * args.port_step
        mtu_ok = ip_packet <= args.mtu
        streams.append(
            {
                "id": index + 1,
                "name": f"stream-{index + 1:02d}",
                "group": group,
                "port": port,
                "payload_type": 96,
                "channel_start": first_channel,
                "channel_end": last_channel,
                "channels": channels,
                "payload_bytes": payload,
                "ip_packet_bytes": ip_packet,
                "mtu_ok": mtu_ok,
            }
        )

    plan = {
        "total_channels": args.total_channels,
        "channels_per_stream": args.channels_per_stream,
        "stream_count": stream_count,
        "sample_rate_hz": args.rate,
        "bits_per_sample": args.bits,
        "encoding": f"L{args.bits}",
        "packet_time_ms": args.ptime_ms,
        "samples_per_packet": samples_per_packet,
        "mtu_bytes": args.mtu,
        "max_payload_for_mtu": max_payload,
        "streams": streams,
    }

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as file:
            json.dump(plan, file, indent=2)
            file.write("\n")

    print("RTP stream split plan")
    print()
    print(f"total_channels:       {args.total_channels}")
    print(f"channels_per_stream:  {args.channels_per_stream}")
    print(f"stream_count:         {stream_count}")
    print(f"sample_rate_hz:       {args.rate}")
    print(f"bits_per_sample:      {args.bits}")
    print(f"packet_time_ms:       {args.ptime_ms:g}")
    print(f"samples_per_packet:   {samples_per_packet}")
    print(f"max_payload_for_mtu:  {max_payload}")
    print()
    print("idx group        port channels    payload ip_packet mtu_ok")

    for stream in streams:
        mtu_ok = "yes" if stream["mtu_ok"] else "no"
        print(
            f"{stream['id']:>3} "
            f"{stream['group']:<12} "
            f"{stream['port']:<5} "
            f"{stream['channel_start']:>3}-{stream['channel_end']:<3} "
            f"{stream['payload_bytes']:>7} "
            f"{stream['ip_packet_bytes']:>9} "
            f"{mtu_ok}"
        )


if __name__ == "__main__":
    main()
