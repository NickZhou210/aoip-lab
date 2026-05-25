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

The sender defaults to 1 ms packets:

```text
48 samples/packet
96 audio payload bytes/packet for mono L16
```

To test 2 channels:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/sender
./send_rtp_audio.sh 127.0.0.1 5004 1000000 2
```

With 1 ms packets, 2-channel L16 should produce `payload_bytes=192` while
`delta_ts` stays `48`.

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

## Phase 3: inspect RTP headers

Terminal 1:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./inspect_rtp_packets.py --group 127.0.0.1 --count 10
```

Terminal 2:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/sender
./send_rtp_audio.sh
```

Use unicast first for RTP header learning. Multicast is a separate network-layer
step and may need VM or switch configuration.

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

1. Multicast across real network interfaces.
2. PTP clock synchronization.
3. Multi-channel scaling.
4. Receiver compatibility testing.

The first SDP example is:

```text
project2_rtp_audio_stream/sdp/rtp-l16-mono.sdp
```
