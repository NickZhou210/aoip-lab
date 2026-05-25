#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-enp0s5}"
DURATION="${2:-8}"
OUTPUT="${3:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CAPTURE_DIR="${REPO_ROOT}/project1_packet_dump/captures"
CONFIG="${REPO_ROOT}/project2_rtp_audio_stream/config/streams.json"

mkdir -p "${CAPTURE_DIR}"

if [ -z "${OUTPUT}" ]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  OUTPUT="${CAPTURE_DIR}/multicast-rtp-${IFACE}-${STAMP}.pcap"
fi

PORT_FILTER="$(
  python3 - "${CONFIG}" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    plan = json.load(handle)

print(" or ".join(f"port {stream['port']}" for stream in plan["streams"]))
PY
)"

FILTER="udp and dst net 224.0.0.0/4 and (${PORT_FILTER})"

echo "Capturing configured multicast RTP..."
echo "Interface: ${IFACE}"
echo "Duration:  ${DURATION}s"
echo "Config:    ${CONFIG}"
echo "Output:    ${OUTPUT}"
echo "Filter:    ${FILTER}"
echo

sudo timeout "${DURATION}" tcpdump -i "${IFACE}" -nn -s 0 "${FILTER}" -w "${OUTPUT}" || status=$?
status="${status:-0}"

if [ "${status}" -ne 0 ] && [ "${status}" -ne 124 ]; then
  exit "${status}"
fi

echo
echo "Capture complete: ${OUTPUT}"
ls -lh "${OUTPUT}"
