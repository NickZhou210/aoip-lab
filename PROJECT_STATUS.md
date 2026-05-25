# Project Status

Last updated: 2026-05-25

## Goal

Build and understand an AES67-style 128-channel AoIP system step by step.

The current architecture target is:

```text
128 channels
= 16 RTP streams
* 8 channels per stream
```

Current audio format:

```text
L16
48 kHz
1 ms packet time
RTP payload type 96
```

## What Is Working

### RTP Audio Basics

Working:

- generate test audio with GStreamer.
- packetize audio as RTP L16.
- send RTP over UDP.
- receive RTP and depayload it.
- write received audio to WAV.

Verified:

```text
1ch L16 / 48 kHz / 1 ms
2ch L16 / 48 kHz / 1 ms
8ch L16 / 48 kHz / 1 ms
```

### RTP Header Inspection

Working:

- inspect RTP version.
- inspect payload type.
- inspect sequence number.
- inspect RTP timestamp.
- inspect SSRC.
- inspect payload bytes.

Important verified result for 1ch:

```text
delta_seq = 1
delta_ts = 48
payload_bytes = 96
```

Important verified result for 2ch:

```text
delta_seq = 1
delta_ts = 48
payload_bytes = 192
```

Important verified result for 8ch:

```text
delta_seq = 1
delta_ts = 48
payload_bytes = 768
```

### Packet Time

Working:

- sender forces 1 ms packet time.

GStreamer settings:

```text
min-ptime=1000000
max-ptime=1000000
ptime-multiple=1000000
```

Meaning:

```text
1 ms = 1,000,000 ns
48 kHz * 1 ms = 48 samples per packet
```

### Bandwidth And MTU Calculation

Working:

- calculate payload size.
- calculate IP packet size.
- estimate wire bandwidth.
- check whether a stream fits a normal 1500-byte MTU.

Important result:

```text
8ch L16 / 1 ms payload = 768 bytes
8ch L16 / 1 ms IP packet = 808 bytes
MTU OK
```

Important warning:

```text
16ch L16 / 1 ms payload = 1536 bytes
16ch L16 / 1 ms IP packet = 1576 bytes
MTU not OK
```

### 128-Channel Stream Plan

Working:

- generate a 128-channel split plan.
- store the plan in JSON.

Config:

```text
project2_rtp_audio_stream/config/streams.json
```

Plan:

```text
stream-01: channels 1-8,     port 5004, group 239.69.1.1
stream-02: channels 9-16,    port 5006, group 239.69.1.2
...
stream-16: channels 121-128, port 5034, group 239.69.1.16
```

### Config-Driven Tools

Working:

- sender reads `streams.json`.
- receiver reads `streams.json`.
- SDP generator reads `streams.json`.
- loopback test runner reads `streams.json`.

Main tools:

```text
project2_rtp_audio_stream/scripts/send_stream_from_config.py
project2_rtp_audio_stream/scripts/receive_stream_from_config.py
project2_rtp_audio_stream/scripts/generate_sdp.py
project2_rtp_audio_stream/scripts/run_stream_pair.py
project2_rtp_audio_stream/scripts/run_all_streams.py
```

### SDP Generation

Working:

- generate one SDP file per RTP stream.

Generated files:

```text
project2_rtp_audio_stream/sdp/generated/stream-01.sdp
...
project2_rtp_audio_stream/sdp/generated/stream-16.sdp
```

Example:

```text
c=IN IP4 239.69.1.1/32
m=audio 5004 RTP/AVP 96
a=rtpmap:96 L16/48000/8
a=ptime:1
a=x-aoip-channel-range:1-8
```

### Local 128-Channel Loopback Test

Working:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_all_streams.py
```

Verified result:

```text
PASS: 16 streams
```

Meaning:

```text
16 streams * 8 channels = 128 channels
```

Each stream locally produced an 8-channel, 48 kHz WAV file.

## What Is Not Done Yet

### PTP

Started.

PTP is required for real AES67 clock synchronization.

Current finding:

```text
enp0s5 has software timestamping only
PTP Hardware Clock: none
linuxptp package is installed
systemd-timesyncd/NTP is active
```

Added:

```text
project3_ptp/scripts/check_ptp_environment.sh
project3_ptp/scripts/run_ptp4l_software.sh
project3_ptp/scripts/query_ptp_status.sh
project3_ptp/configs/aes67-software-ptp.cfg
project3_ptp/notes/phase15_ptp_first_checks.md
project3_ptp/notes/phase16_run_ptp4l_software.md
project3_ptp/notes/phase17_query_ptp_status.md
```

First `ptp4l` observe run:

```text
enp0s5 INITIALIZING -> LISTENING -> MASTER
selected local clock 001c42.fffe.ee3f40 as best master
assuming the grand master role
```

Meaning:

```text
ptp4l runs successfully
no external better PTP grandmaster was visible
the VM became the local software grandmaster
```

First `pmc` query:

```text
PORT_DATA_SET:    portState MASTER
CURRENT_DATA_SET: stepsRemoved 0, offsetFromMaster 0.0, meanPathDelay 0.0
PARENT_DATA_SET:  grandmasterIdentity 001c42.fffe.ee3f40
TIME_STATUS_NP:   gmPresent false
```

Meaning:

```text
pmc can query the running ptp4l process
the VM is the current software grandmaster
there is no external grandmaster visible yet
```

### PTP BMCA Grandmaster Selection

Started.

Added:

```text
project3_ptp/scripts/compare_ptp_clocks.py
project3_ptp/notes/phase24_ptp_bmca.md
```

Current learning target:

```text
BMCA decides the Grandmaster from priority1, clock quality, priority2, and clock identity
lower values win at the first field that differs
```

### PTP Config Experiments

Started.

Added:

```text
project3_ptp/configs/aes67-preferred-master.cfg
project3_ptp/configs/aes67-backup-master.cfg
project3_ptp/configs/aes67-domain-1.cfg
project3_ptp/configs/aes67-client-only.cfg
project3_ptp/scripts/summarize_ptp_configs.py
project3_ptp/notes/phase25_ptp_config_experiments.md
```

Current learning target:

```text
priority controls BMCA preference
domainNumber separates timing islands
clientOnly prevents a node from becoming Grandmaster
```

Verified:

```text
summarize_ptp_configs.py reads all five config files on Ubuntu
sudo is required for live ptp4l config start tests
preferred-master manually reached MASTER
client-only manually started and did not show LISTENING to MASTER in the 8 second window
```

### PTP Domain Experiment

Started.

Added:

```text
project3_ptp/notes/phase26_ptp_domain_experiment.md
```

Current learning target:

```text
domainNumber separates independent PTP timing islands
sender and receiver must use the same PTP domain to share clock
```

Verified:

```text
aes67-domain-1.cfg manually reached MASTER
VM becomes Grandmaster in domain 1 when no external domain 1 master is visible
```

### PTP Status Snapshot

Started.

Added:

```text
project3_ptp/scripts/ptp_status_snapshot.py
project3_ptp/notes/phase27_ptp_status_snapshot.md
```

Current learning target:

```text
one command should report ptp4l process state, portState, Grandmaster identity, offset, and path delay
```

Verified:

```text
ptp_status_snapshot.py queried running ptp4l on domain 0
portState MASTER
grandmasterIdentity 001c42.fffe.ee3f40
offsetFromMaster 0.0
meanPathDelay 0.0
```

### RTP Timestamp And PTP Time

Started.

Added:

```text
project3_ptp/scripts/observe_rtp_timestamp_clock.py
project3_ptp/notes/phase18_rtp_timestamp_vs_ptp_time.md
```

Current learning target:

```text
PTP time is the shared wall clock
RTP timestamp is the audio media clock
48 kHz audio advances 48 RTP timestamp ticks per 1 ms packet
```

Verified with stream-01:

```text
delta_ts = 48
rtp_elapsed_ms advances by 1 ms per packet
payload_bytes = 768
```

### Receiver Playout Timing

Started.

Added:

```text
project3_ptp/scripts/calculate_playout_schedule.py
project3_ptp/notes/phase19_receiver_playout_timing.md
```

Updated:

```text
project2_rtp_audio_stream/scripts/generate_sdp.py can optionally emit RFC 7273 clock lines
```

Current learning target:

```text
RTP timestamp + PTP anchor + receiver latency = scheduled playback time
```

### Multi-Stream PTP Alignment

Started.

Added:

```text
project3_ptp/scripts/calculate_multistream_alignment.py
project3_ptp/notes/phase20_multistream_ptp_alignment.md
```

Current learning target:

```text
16 RTP streams are aligned when equivalent RTP media times map to the same PTP playout time
packet arrival time is not the alignment reference
```

Still needed:

- understand master/slave behavior.
- measure offset.
- decide how GStreamer sender should relate to PTP time.

### Real Multicast Network Testing

Partially explored, not solved.

Current local loopback tests use:

```text
127.0.0.1
```

Multicast config exists:

```text
239.69.1.1 ... 239.69.1.16
```

Still needed:

- solve VM multicast behavior.
- test multicast on `enp0s5`.
- verify multicast traffic with tcpdump/Wireshark.
- test multicast between two machines or VM and host if possible.

### Multi-Stream Synchronization

Started.

We can test 16 streams one after another, but not yet all at the same time.

Added:

```text
project2_rtp_audio_stream/scripts/run_concurrent_senders.py
project2_rtp_audio_stream/notes/phase21_concurrent_senders.md
```

Verified:

```text
started_count: 16
PASS: 16 senders ran concurrently
gst_count=0
sender_count=0
```

Added:

```text
project2_rtp_audio_stream/scripts/monitor_all_streams.py
project2_rtp_audio_stream/scripts/run_concurrent_sender_monitor.py
project2_rtp_audio_stream/notes/phase22_monitor_all_streams.md
```

Verified:

```text
PASS: 16 streams reached 20 packets
each stream: payload_bytes = 768
each stream: delta_seq = 1
each stream: delta_ts = 48
gst_count=0
sender_count=0
```

Added:

```text
project2_rtp_audio_stream/scripts/run_sender_performance_probe.py
project2_rtp_audio_stream/notes/phase23_sender_performance_probe.md
```

Verified:

```text
avg_cpu_percent:       13.79
avg_tx_mbps on lo:     177.698
avg_rx_mbps on lo:     177.698
peak_sender_rss_mib:   384.4
gst_count=0
sender_count=0
```

Still needed:

- check stream alignment conceptually.
- connect this to PTP.

### Full AES67 Interoperability

Not done.

Still needed:

- confirm SDP compatibility with real AES67 tools/devices.
- confirm packet time expectations.
- confirm L16 vs L24 requirements for target devices.
- add receiver tests using external AES67/Ravenna/Dante-compatible software if available.

### SAP / Discovery

Not done.

Currently SDP files are generated manually.

Still needed:

- decide whether to implement SAP announcement.
- or load SDP manually in receiver software.

## Current Mental Model

```text
RTP = audio packet transport
SDP = description of each RTP stream
PTP = shared clock for real synchronized playback
Multicast = network delivery method for shared streams
```

Current project has strong progress on:

```text
RTP
SDP generation
128-channel stream planning
local loopback verification
```

Next major topic:

```text
PTP
```
