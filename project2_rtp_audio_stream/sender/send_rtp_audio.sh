#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-127.0.0.1}"
PORT="${2:-5004}"

echo "Starting RTP L16 sender..."
echo "Destination: ${HOST}:${PORT}"
echo "Format: 48 kHz, mono, 16-bit big-endian, RTP payload type 96"

gst-launch-1.0 \
audiotestsrc wave=sine freq=1000 is-live=true ! \
audio/x-raw,format=S16BE,rate=48000,channels=1 ! \
rtpL16pay pt=96 ! \
udpsink host="${HOST}" port="${PORT}"
