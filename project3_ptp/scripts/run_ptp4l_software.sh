#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-enp0s5}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG="${PROJECT_DIR}/configs/aes67-software-ptp.cfg"

echo "Starting ptp4l software timestamp learning run"
echo "Interface: ${IFACE}"
echo "Config: ${CONFIG}"
echo
echo "This run uses free_running=1, so ptp4l observes PTP behavior without adjusting the local clock."
echo "Stop with Ctrl+C."
echo

exec sudo ptp4l -i "${IFACE}" -f "${CONFIG}" -m
