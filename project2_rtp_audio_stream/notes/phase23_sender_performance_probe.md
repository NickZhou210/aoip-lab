# Phase 23: Sender Performance Probe

Phase 21 proved:

```text
16 senders can run concurrently
```

Phase 22 proved:

```text
all 16 streams produce valid RTP headers
```

Phase 23 measures basic runtime cost:

```text
CPU
sender memory
loopback TX/RX bitrate
```

## Run Command

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_sender_performance_probe.py --duration 5 --interval 1
```

Default behavior:

```text
host = 127.0.0.1
sample_iface = lo
```

This matches the current local unicast test.

## Expected Bitrate

Current stream plan:

```text
16 streams
8 channels per stream
L16
48 kHz
1 ms packet time
```

Payload rate:

```text
768 bytes/packet * 1000 packets/s * 16 streams
= 12,288,000 bytes/s
= 98.304 Mbit/s
```

Approximate IP packet rate:

```text
808 bytes/packet * 1000 packets/s * 16 streams
= 12,928,000 bytes/s
= 103.424 Mbit/s
```

Local loopback interface counters are not the same as real Ethernet wire rate,
but they give a useful sanity check.

## What This Measures

The probe reads:

```text
/proc/stat
/proc/net/dev
/proc/<pid>/status
```

It reports:

```text
cpu_percent
tx_mbps
rx_mbps
sender_processes
sender_rss_mib
```

## What This Does Not Prove

This still does not prove:

```text
multicast switch performance
hardware timestamp quality
receiver playback stability
external AES67 interoperability
```

It only measures the local VM cost of generating the current 16-stream sender
set.

## Observed Result On Ubuntu

Command:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_sender_performance_probe.py --duration 5 --interval 1
```

Observed:

```text
expected_payload_mbps:  98.304
expected_ip_mbps:       103.424

sample cpu_percent tx_mbps rx_mbps sender_processes sender_rss_mib
000001       12.96 177.202 177.202               33          384.4
000002       12.35 177.942 177.942               33          384.4
000003       13.58 177.752 177.752               33          384.4
000004       14.20 177.841 177.841               33          384.4
000005       15.85 177.750 177.750               33          384.4

avg_cpu_percent:       13.79
avg_tx_mbps:           177.698
avg_rx_mbps:           177.698
peak_sender_rss_mib:   384.4
```

Cleanup check:

```text
gst_count=0
sender_count=0
```

Interpretation:

```text
CPU load was moderate for the VM in this short local test
sender memory was about 384 MiB for the Python and GStreamer sender processes
loopback bitrate was higher than the calculated IP payload estimate
```

The loopback bitrate should not be treated as Ethernet wire rate. Linux loopback
interface counters include local kernel accounting behavior and are useful as a
repeatable local baseline, not as a final network-capacity measurement.

The important practical result:

```text
the VM can generate the current 16-stream 128-channel RTP sender set for this short test
```
