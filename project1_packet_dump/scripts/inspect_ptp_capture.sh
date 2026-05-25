#!/usr/bin/env bash
set -euo pipefail

PCAP="${1:-}"
COUNT="${2:-40}"

if [ -z "${PCAP}" ]; then
  echo "Usage: $0 <capture.pcap> [packet_count]" >&2
  exit 2
fi

echo "Inspecting PTP capture..."
echo "Capture: ${PCAP}"
echo "Packet count: ${COUNT}"
echo

tcpdump -nn -tttt -r "${PCAP}" -c "${COUNT}" "(udp port 319 or udp port 320)"
