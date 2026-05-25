#!/usr/bin/env bash
set -euo pipefail

GROUP="${1:-239.69.1.1}"
PORT="${2:-5004}"

echo "Starting multicast RTP L16 sender..."
echo "Destination: ${GROUP}:${PORT}"
echo "Format: 48 kHz, mono, 16-bit big-endian, RTP payload type 96"

gst-launch-1.0 -v \
audiotestsrc wave=sine freq=1000 is-live=true ! \
audio/x-raw,format=S16BE,rate=48000,channels=1 ! \
rtpL16pay pt=96 ! \
udpsink host="${GROUP}" port="${PORT}" auto-multicast=true ttl-mc=16

