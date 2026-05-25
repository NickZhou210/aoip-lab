#!/usr/bin/env python3
"""Calculate basic RTP/AES67 stream sizes.

This intentionally uses simple visible math so the numbers can be checked by
hand while learning.
"""

from __future__ import annotations

import argparse
import math


ETHERNET_HEADER_BYTES = 14
IPV4_HEADER_BYTES = 20
UDP_HEADER_BYTES = 8
RTP_HEADER_BYTES = 12
ETHERNET_FCS_BYTES = 4
PREAMBLE_AND_IFG_BYTES = 20
DEFAULT_MTU_BYTES = 1500


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate RTP audio stream sizes")
    parser.add_argument("--rate", type=int, default=48000, help="sample rate in Hz")
    parser.add_argument("--bits", type=int, default=16, choices=(16, 24), help="bits per sample")
    parser.add_argument("--channels", type=int, default=2, help="audio channels")
    parser.add_argument("--ptime-ms", type=float, default=1.0, help="packet time in milliseconds")
    parser.add_argument("--mtu", type=int, default=DEFAULT_MTU_BYTES, help="IP MTU bytes")
    return parser.parse_args()


def fmt_mbps(bits_per_second: float) -> str:
    return f"{bits_per_second / 1_000_000:.3f} Mbit/s"


def main() -> None:
    args = parse_args()

    bytes_per_sample = args.bits // 8
    packet_time_seconds = args.ptime_ms / 1000
    packets_per_second = 1 / packet_time_seconds
    samples_per_packet_exact = args.rate * packet_time_seconds
    samples_per_packet = int(round(samples_per_packet_exact))

    payload_bytes = samples_per_packet * bytes_per_sample * args.channels
    rtp_udp_ip_bytes = RTP_HEADER_BYTES + UDP_HEADER_BYTES + IPV4_HEADER_BYTES
    ip_packet_bytes = payload_bytes + rtp_udp_ip_bytes
    ethernet_frame_bytes = ETHERNET_HEADER_BYTES + ip_packet_bytes + ETHERNET_FCS_BYTES
    wire_bytes = ethernet_frame_bytes + PREAMBLE_AND_IFG_BYTES

    audio_bits_per_second = args.rate * bytes_per_sample * args.channels * 8
    ip_bits_per_second = ip_packet_bytes * packets_per_second * 8
    wire_bits_per_second = wire_bytes * packets_per_second * 8

    fits_mtu = ip_packet_bytes <= args.mtu
    max_payload_for_mtu = args.mtu - rtp_udp_ip_bytes
    streams_needed_for_mtu = math.ceil(payload_bytes / max_payload_for_mtu) if max_payload_for_mtu > 0 else 0

    print("RTP audio stream calculator")
    print()
    print(f"sample_rate_hz:          {args.rate}")
    print(f"bits_per_sample:         {args.bits}")
    print(f"bytes_per_sample:        {bytes_per_sample}")
    print(f"channels:                {args.channels}")
    print(f"packet_time_ms:          {args.ptime_ms:g}")
    print(f"packets_per_second:      {packets_per_second:.3f}")
    print(f"samples_per_packet:      {samples_per_packet}")
    print()
    print(f"audio_payload_bytes:     {payload_bytes}")
    print(f"rtp_udp_ip_header_bytes: {rtp_udp_ip_bytes}")
    print(f"ip_packet_bytes:         {ip_packet_bytes}")
    print(f"ethernet_frame_bytes:    {ethernet_frame_bytes}")
    print(f"wire_bytes_per_packet:   {wire_bytes}")
    print()
    print(f"audio_bandwidth:         {fmt_mbps(audio_bits_per_second)}")
    print(f"ip_bandwidth:            {fmt_mbps(ip_bits_per_second)}")
    print(f"wire_bandwidth_estimate: {fmt_mbps(wire_bits_per_second)}")
    print()
    print(f"mtu_bytes:               {args.mtu}")
    print(f"max_payload_for_mtu:     {max_payload_for_mtu}")
    print(f"fits_single_ip_packet:   {'yes' if fits_mtu else 'no'}")

    if not fits_mtu:
        print(f"minimum_streams_by_mtu:  {streams_needed_for_mtu}")
        print("warning: payload is larger than the MTU allows in one normal IP packet")


if __name__ == "__main__":
    main()

