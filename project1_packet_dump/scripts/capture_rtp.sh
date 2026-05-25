#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-any}"
PORT="${2:-5004}"
OUTPUT="${3:-../captures/rtp_capture.pcap}"

echo "Starting RTP capture..."
echo "Interface: ${IFACE}"
echo "UDP port: ${PORT}"
echo "Output: ${OUTPUT}"

sudo tcpdump -i "${IFACE}" -nn "udp port ${PORT}" -w "${OUTPUT}"
