# AOIP / AES67 Lab

This repo is a learning lab for RTP audio, packet capture, and AES67 building blocks.

## Current progress

- `project1_packet_dump`: tcpdump helpers for RTP, PTP, and general packet capture.
- `project2_rtp_audio_stream`: GStreamer RTP L16 sender and receiver.
- Phase 1 is complete: local RTP L16 loopback can create a WAV file.

Start with [LEARNING_MAP.md](LEARNING_MAP.md) if you want the full logic of how these pieces relate to AoIP and AES67.

## Phase 1: local RTP L16 loopback

Terminal 1:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/receiver
./receive_rtp_audio.sh
```

Terminal 2:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/sender
./send_rtp_audio.sh
```

Stop both with `Ctrl+C`, then check:

```bash
ls -lh ~/aoip-lab/project2_rtp_audio_stream/receiver/test.wav
file ~/aoip-lab/project2_rtp_audio_stream/receiver/test.wav
```

## Phase 2: multicast RTP L16

Terminal 1:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/receiver
./receive_multicast_rtp_audio.sh
```

Terminal 2:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/sender
./send_multicast_rtp_audio.sh
```

This uses multicast group `239.69.1.1` and UDP port `5004`.

## Capture RTP

```bash
cd ~/aoip-lab/project1_packet_dump/scripts
./live_rtp_monitor.sh
```

or save a capture:

```bash
./capture_rtp.sh
```

## AES67 notes

This is not full AES67 yet. It currently covers the RTP audio layer only.
Next AES67 steps are:

1. Fixed SDP description.
2. Packet time verification.
3. Multicast across real network interfaces.
4. PTP clock synchronization.

The first SDP example is:

```text
project2_rtp_audio_stream/sdp/rtp-l16-mono.sdp
```
