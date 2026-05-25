#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-any}"
OUTPUT="${2:-../captures/ptp_capture.pcap}"

echo "Capturing PTP..."
echo "Interface: ${IFACE}"
echo "Output: ${OUTPUT}"

sudo tcpdump -i "${IFACE}" -nn "(udp port 319 or udp port 320)" -w "${OUTPUT}"
