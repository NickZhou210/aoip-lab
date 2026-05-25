#!/usr/bin/env bash
set -euo pipefail

GROUP="${1:-239.69.1.1}"
PORT="${2:-5004}"
OUTPUT="${3:-test-multicast.wav}"

echo "Starting multicast RTP L16 receiver..."
echo "Group: ${GROUP}"
echo "Listening on UDP port ${PORT}"
echo "Writing WAV file: ${OUTPUT}"

gst-launch-1.0 -v \
udpsrc multicast-group="${GROUP}" auto-multicast=true port="${PORT}" \
caps="application/x-rtp,media=audio,encoding-name=L16,clock-rate=48000,channels=1,payload=96" ! \
rtpjitterbuffer latency=50 ! \
rtpL16depay ! \
audioconvert ! \
wavenc ! \
filesink location="${OUTPUT}"

