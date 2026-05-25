#!/usr/bin/env bash
set -euo pipefail

PCAP="${1:-}"
COUNT="${2:-10}"

if [ -z "${PCAP}" ]; then
  echo "Usage: $0 <capture.pcap> [packet_preview_count]" >&2
  exit 2
fi

if [ ! -f "${PCAP}" ]; then
  echo "Capture file not found: ${PCAP}" >&2
  exit 2
fi

echo "PTP capture summary"
echo "Capture: ${PCAP}"
echo

echo "== File =="
ls -lh "${PCAP}"
file "${PCAP}"
echo

echo "== Packet Counts =="
total="$(tcpdump -nn -r "${PCAP}" "(udp port 319 or udp port 320)" 2>/dev/null | wc -l | tr -d ' ')"
event="$(tcpdump -nn -r "${PCAP}" "udp port 319" 2>/dev/null | wc -l | tr -d ' ')"
general="$(tcpdump -nn -r "${PCAP}" "udp port 320" 2>/dev/null | wc -l | tr -d ' ')"
echo "udp_319_320_total: ${total}"
echo "udp_319_event:     ${event}"
echo "udp_320_general:   ${general}"
echo

echo "== Preview =="
tcpdump -nn -tttt -r "${PCAP}" -c "${COUNT}" "(udp port 319 or udp port 320)"
