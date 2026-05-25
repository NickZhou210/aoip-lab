#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-any}"

echo "Monitoring PTP traffic..."
echo "Interface: ${IFACE}"
echo "Filter: udp port 319 or udp port 320"
echo

sudo tcpdump -i "${IFACE}" -nn -vv "(udp port 319 or udp port 320)"
