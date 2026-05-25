#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-enp0s5}"
IFACE_IP="${2:-10.211.55.6}"
DURATION="${3:-12}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CAPTURE_DIR="${REPO_ROOT}/project1_packet_dump/captures"
PTP_CONFIG="${REPO_ROOT}/project3_ptp/configs/aes67-software-ptp.cfg"
LOG_DIR="${REPO_ROOT}/project3_ptp/logs"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT="${CAPTURE_DIR}/ptp-and-multicast-rtp-${IFACE}-${STAMP}.pcap"
PTP_LOG="${LOG_DIR}/ptp4l-phase31-${IFACE}-${STAMP}.log"
STARTED_PTP=0
PTP_PID=""

mkdir -p "${CAPTURE_DIR}" "${LOG_DIR}"

echo "Phase 31 PTP plus multicast RTP capture test"
echo "Interface:    ${IFACE}"
echo "Interface IP: ${IFACE_IP}"
echo "Duration:     ${DURATION}s"
echo "Output:       ${OUTPUT}"
echo "PTP config:   ${PTP_CONFIG}"
echo

sudo -v

cleanup() {
  if [ -n "${CAPTURE_PID:-}" ] && kill -0 "${CAPTURE_PID}" 2>/dev/null; then
    sudo kill "${CAPTURE_PID}" 2>/dev/null || true
  fi
  if [ "${STARTED_PTP}" -eq 1 ] && [ -n "${PTP_PID}" ] && kill -0 "${PTP_PID}" 2>/dev/null; then
    sudo kill "${PTP_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if pgrep -x ptp4l >/dev/null; then
  echo "Using existing ptp4l process."
else
  echo "Starting temporary ptp4l process."
  sudo ptp4l -i "${IFACE}" -f "${PTP_CONFIG}" -m >"${PTP_LOG}" 2>&1 &
  PTP_PID="$!"
  STARTED_PTP=1
  sleep 2
fi

"${SCRIPT_DIR}/capture_ptp_and_multicast_rtp.sh" "${IFACE}" "${DURATION}" "${OUTPUT}" &
CAPTURE_PID="$!"

sleep 2

"${REPO_ROOT}/project2_rtp_audio_stream/scripts/run_concurrent_sender_monitor.py" \
  --use-config-groups \
  --iface "${IFACE}" \
  --iface-ip "${IFACE_IP}" \
  --count 20 \
  --sender-duration 6 \
  --monitor-timeout 5

wait "${CAPTURE_PID}" || status=$?
status="${status:-0}"

if [ "${STARTED_PTP}" -eq 1 ] && [ -n "${PTP_PID}" ] && kill -0 "${PTP_PID}" 2>/dev/null; then
  sudo kill "${PTP_PID}" 2>/dev/null || true
  wait "${PTP_PID}" 2>/dev/null || true
fi
trap - EXIT

if [ "${status}" -ne 0 ] && [ "${status}" -ne 124 ]; then
  exit "${status}"
fi

echo
"${SCRIPT_DIR}/summarize_ptp_capture.sh" "${OUTPUT}" 8
echo
"${SCRIPT_DIR}/summarize_multicast_rtp_capture.py" "${OUTPUT}"

if [ "${STARTED_PTP}" -eq 1 ]; then
  echo
  echo "Temporary ptp4l log: ${PTP_LOG}"
fi
