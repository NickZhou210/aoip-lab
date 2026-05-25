#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-any}"
PORT="${2:-5004}"

echo "Monitoring RTP traffic..."
echo "Interface: ${IFACE}"
echo "UDP port: ${PORT}"

sudo tcpdump -i "${IFACE}" -nn "udp port ${PORT}"
