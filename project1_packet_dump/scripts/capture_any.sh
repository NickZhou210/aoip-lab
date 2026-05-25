#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-any}"
OUTPUT="${2:-../captures/network_capture.pcap}"

echo "Starting network capture..."
echo "Interface: ${IFACE}"
echo "Output: ${OUTPUT}"

sudo tcpdump -i "${IFACE}" -nn -w "${OUTPUT}"
