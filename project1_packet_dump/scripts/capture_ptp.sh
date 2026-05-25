#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-any}"
DURATION="${2:-10}"
OUTPUT="${3:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAPTURE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)/captures"

mkdir -p "${CAPTURE_DIR}"

if [ -z "${OUTPUT}" ]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  OUTPUT="${CAPTURE_DIR}/ptp-${IFACE}-${STAMP}.pcap"
fi

echo "Capturing PTP..."
echo "Interface: ${IFACE}"
echo "Duration: ${DURATION}s"
echo "Output: ${OUTPUT}"
echo "Filter: udp port 319 or udp port 320"
echo

sudo timeout "${DURATION}" tcpdump -i "${IFACE}" -nn -s 0 "(udp port 319 or udp port 320)" -w "${OUTPUT}" || status=$?
status="${status:-0}"

if [ "${status}" -ne 0 ] && [ "${status}" -ne 124 ]; then
  exit "${status}"
fi

echo
echo "Capture complete: ${OUTPUT}"
ls -lh "${OUTPUT}"
