# AOIP / AES67 Lab

This repo is a learning lab for RTP audio, packet capture, and AES67 building blocks.

## Philosophy

This project is built as a learning lab, not as a production-grade AES67 implementation.

I am a live sound / pro-audio engineer learning networked audio from the packet level upward.  
Some parts are AI-assisted, but every committed phase should be reproducible, observable, and gradually explainable.

The goal is not to pretend mastery, but to reduce the black box around AOIP systems for myself and other audio engineers.

Current milestone status:

```text
PROJECT_STATUS.md
```

## Current progress

- `project1_packet_dump`: tcpdump helpers for RTP, PTP, and general packet capture.
- `project2_rtp_audio_stream`: GStreamer RTP L16 sender and receiver.
- `project3_ptp`: PTP environment checks and learning notes.
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

## Phase 4: calculate bandwidth and MTU

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./calc_stream.py --channels 2
./calc_stream.py --channels 128
```

This shows why 128 channels cannot simply be treated as one ordinary small RTP
packet stream on a normal 1500-byte MTU network.

## Phase 5: plan stream splitting

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./plan_streams.py --total-channels 128 --channels-per-stream 8
```

This creates a first 128-channel layout:

```text
16 RTP streams * 8 channels each
```

The current generated config is:

```text
project2_rtp_audio_stream/config/streams.json
```

## Phase 6: send one stream from config

Terminal 1:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./inspect_rtp_packets.py --group 127.0.0.1 --port 5004 --count 10
```

Terminal 2:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./send_stream_from_config.py --stream 1 --host 127.0.0.1
```

For stream 1, expect `payload_bytes=768` and `delta_ts=48`.

To receive stream 1:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./receive_stream_from_config.py --stream 1
```

## Phase 7: generate SDP files

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./generate_sdp.py
```

Generated files go to:

```text
project2_rtp_audio_stream/sdp/generated/
```

## Phase 8: run a loopback test

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_stream_pair.py --stream 1
```

This starts receiver and sender for one configured stream, then checks the WAV
output.

To test every configured stream:

```bash
./run_all_streams.py
```

## Phase 9: first PTP check

```bash
cd ~/aoip-lab/project3_ptp/scripts
./check_ptp_environment.sh enp0s5
```

This confirms whether `ptp4l`, `phc2sys`, and `pmc` are installed, and whether
the VM network interface has hardware or software timestamping.

## Phase 10: run ptp4l in observe mode

```bash
cd ~/aoip-lab/project3_ptp/scripts
./run_ptp4l_software.sh enp0s5
```

This starts `ptp4l` with software timestamping and `free_running=1`, so the first
PTP lesson can observe logs without intentionally disciplining the system clock.

## Phase 11: query ptp4l status

Keep `ptp4l` running in one terminal, then in a second terminal:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./query_ptp_status.sh
```

This uses `pmc` to ask the running `ptp4l` process for its port, parent, current
time, and grandmaster status.

## Phase 12: observe RTP timestamp as audio time

Terminal 1:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./observe_rtp_timestamp_clock.py --group 127.0.0.1 --port 5004 --count 20
```

Terminal 2:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./send_stream_from_config.py --stream 1 --host 127.0.0.1
```

For stream 1, the RTP timestamp should advance by `48` per packet while the
payload remains `768` bytes.

## Phase 13: receiver playout timing model

```bash
cd ~/aoip-lab/project3_ptp/scripts
./calculate_playout_schedule.py --count 5
```

This shows the receiver-side idea:

```text
RTP timestamp + PTP anchor + receiver latency = scheduled playback time
```

To generate SDP with RFC 7273 clock lines:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./generate_sdp.py --output-dir ../sdp/generated-ptp --ptp-grandmaster 001c42.fffe.ee3f40
```

## Phase 14: multi-stream PTP alignment model

```bash
cd ~/aoip-lab/project3_ptp/scripts
./calculate_multistream_alignment.py --packet-index 100
```

To demonstrate a 1 ms stream offset:

```bash
./calculate_multistream_alignment.py --packet-index 100 --skew-stream 2 --skew-samples 48
```

## Phase 15: run 16 RTP senders concurrently

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_concurrent_senders.py --duration 5
```

This starts all 16 configured 8-channel RTP senders at the same time, using
local unicast by default.

## Phase 16: monitor all 16 RTP streams

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_concurrent_sender_monitor.py --count 20
```

This verifies each configured stream reaches 20 RTP packets with
`payload_bytes=768` and `delta_ts=48`.

For multicast groups from `streams.json`:

```bash
./run_concurrent_sender_monitor.py --use-config-groups --iface enp0s5 --iface-ip 10.211.55.6 --count 20
```

To capture and summarize the 16 multicast RTP streams on the VM interface:

```bash
cd ~/aoip-lab
project1_packet_dump/scripts/run_multicast_rtp_capture_test.sh enp0s5 10.211.55.6 8
```

To capture PTP and the 16 multicast RTP streams in the same pcap:

```bash
cd ~/aoip-lab
project1_packet_dump/scripts/run_ptp_rtp_capture_test.sh enp0s5 10.211.55.6 12
```

To derive an RTP timestamp to reference-time anchor from that pcap:

```bash
cd ~/aoip-lab
project3_ptp/scripts/derive_rtp_ptp_anchor_from_pcap.py project1_packet_dump/captures/<combined-ptp-rtp-capture>.pcap
```

To generate and validate SDP files with PTP clock reference lines:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./generate_sdp.py --output-dir ../sdp/generated-ptp --ptp-grandmaster 001c42.fffe.ee3f40 --ptp-domain 0 --mediaclk-direct 0
./validate_sdp_clock_lines.py --sdp-dir ../sdp/generated-ptp --ptp-grandmaster 001c42.fffe.ee3f40 --ptp-domain 0 --mediaclk-direct 0
```

## Phase 17: sender performance probe

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_sender_performance_probe.py --duration 5 --interval 1
```

This measures basic CPU, memory, and loopback bitrate while the 16 RTP senders
are running.

## Phase 18: PTP BMCA model

```bash
cd ~/aoip-lab/project3_ptp/scripts
./compare_ptp_clocks.py
```

This models how PTP chooses a Grandmaster from priority and clock quality fields.

## Phase 19: PTP config experiments

```bash
cd ~/aoip-lab/project3_ptp/scripts
./summarize_ptp_configs.py
```

This compares the learning `ptp4l` configs for priority, domain, and client-only
behavior.

## Phase 20: PTP domain experiment

```bash
cd ~/aoip-lab/project3_ptp
sudo timeout 8s ptp4l -i enp0s5 -f configs/aes67-domain-1.cfg -m
```

This checks that the domain 1 config starts and forms its own timing island.

## Phase 21: PTP status snapshot

```bash
cd ~/aoip-lab/project3_ptp/scripts
./ptp_status_snapshot.py --domain 0
```

This summarizes `ptp4l` and `pmc` status in one command.

## Phase 22: capture PTP packets

```bash
cd ~/aoip-lab/project1_packet_dump/scripts
./capture_ptp.sh enp0s5 10
```

This saves a tcpdump capture for UDP 319/320 PTP traffic.

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
