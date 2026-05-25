#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-5004}"
OUTPUT="${2:-test.wav}"
CHANNELS="${3:-1}"

echo "Starting RTP L16 receiver..."
echo "Listening on UDP port ${PORT}"
echo "Writing WAV file: ${OUTPUT}"
echo "Channels: ${CHANNELS}"

gst-launch-1.0 \
udpsrc port="${PORT}" caps="application/x-rtp,media=audio,encoding-name=L16,clock-rate=48000,channels=${CHANNELS},payload=96" ! \
rtpjitterbuffer latency=50 ! \
rtpL16depay ! \
audioconvert ! \
wavenc ! \
filesink location="${OUTPUT}"
