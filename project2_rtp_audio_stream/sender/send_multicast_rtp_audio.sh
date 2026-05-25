#!/usr/bin/env bash
set -euo pipefail

GROUP="${1:-239.69.1.1}"
PORT="${2:-5004}"
IFACE="${3:-enp0s5}"
PTIME_NS="${4:-1000000}"
CHANNELS="${5:-1}"

echo "Starting multicast RTP L16 sender..."
echo "Destination: ${GROUP}:${PORT}"
echo "Interface: ${IFACE}"
echo "Format: 48 kHz, ${CHANNELS} channel(s), 16-bit big-endian, RTP payload type 96"
echo "Packet time: ${PTIME_NS} ns"

gst-launch-1.0 -v \
audiotestsrc wave=sine freq=1000 is-live=true ! \
audio/x-raw,format=S16BE,rate=48000,channels="${CHANNELS}" ! \
rtpL16pay pt=96 min-ptime="${PTIME_NS}" max-ptime="${PTIME_NS}" ptime-multiple="${PTIME_NS}" mtu=1200 ! \
udpsink host="${GROUP}" port="${PORT}" auto-multicast=true multicast-iface="${IFACE}" loop=true ttl-mc=16
