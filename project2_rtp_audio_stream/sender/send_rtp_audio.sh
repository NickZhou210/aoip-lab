#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-127.0.0.1}"
PORT="${2:-5004}"
PTIME_NS="${3:-1000000}"
CHANNELS="${4:-1}"

echo "Starting RTP L16 sender..."
echo "Destination: ${HOST}:${PORT}"
echo "Format: 48 kHz, ${CHANNELS} channel(s), 16-bit big-endian, RTP payload type 96"
echo "Packet time: ${PTIME_NS} ns"

gst-launch-1.0 \
audiotestsrc wave=sine freq=1000 is-live=true ! \
audio/x-raw,format=S16BE,rate=48000,channels="${CHANNELS}" ! \
rtpL16pay pt=96 min-ptime="${PTIME_NS}" max-ptime="${PTIME_NS}" ptime-multiple="${PTIME_NS}" mtu=1200 ! \
udpsink host="${HOST}" port="${PORT}"
