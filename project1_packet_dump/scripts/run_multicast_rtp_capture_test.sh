#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-enp0s5}"
IFACE_IP="${2:-10.211.55.6}"
DURATION="${3:-8}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CAPTURE_DIR="${REPO_ROOT}/project1_packet_dump/captures"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT="${CAPTURE_DIR}/multicast-rtp-${IFACE}-${STAMP}.pcap"

mkdir -p "${CAPTURE_DIR}"

echo "Phase 30 multicast RTP capture test"
echo "Interface:    ${IFACE}"
echo "Interface IP: ${IFACE_IP}"
echo "Duration:     ${DURATION}s"
echo "Output:       ${OUTPUT}"
echo

sudo -v

"${SCRIPT_DIR}/capture_multicast_rtp_16.sh" "${IFACE}" "${DURATION}" "${OUTPUT}" &
CAPTURE_PID="$!"

cleanup() {
  if kill -0 "${CAPTURE_PID}" 2>/dev/null; then
    sudo kill "${CAPTURE_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

sleep 1

"${REPO_ROOT}/project2_rtp_audio_stream/scripts/run_concurrent_sender_monitor.py" \
  --use-config-groups \
  --iface "${IFACE}" \
  --iface-ip "${IFACE_IP}" \
  --count 20 \
  --sender-duration 6 \
  --monitor-timeout 5

wait "${CAPTURE_PID}" || status=$?
status="${status:-0}"
trap - EXIT

if [ "${status}" -ne 0 ] && [ "${status}" -ne 124 ]; then
  exit "${status}"
fi

echo
"${SCRIPT_DIR}/summarize_multicast_rtp_capture.py" "${OUTPUT}"
