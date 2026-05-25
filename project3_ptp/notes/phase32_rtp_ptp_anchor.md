# Phase 32: RTP Timestamp to PTP Time Anchor

Phase 31 proved that PTP traffic and RTP traffic can coexist in one capture.

Phase 32 explains the next timing concept:

```text
RTP timestamp is media sample time.
PTP time is shared network time.
An AES67 receiver needs an anchor connecting the two.
```

## The Anchor

The basic relationship is:

```text
RTP timestamp R0 corresponds to reference time T0
```

After that, any RTP timestamp can be mapped:

```text
media_elapsed_seconds = (rtp_timestamp - R0) / sample_rate
scheduled_playout_time = T0 + media_elapsed_seconds + receiver_latency
```

For our current stream plan:

```text
sample_rate = 48000 Hz
packet_time = 1 ms
samples_per_packet = 48
```

So each RTP packet should advance:

```text
48 samples / 48000 samples per second = 1 ms
```

## Lab Tool

Run this against the combined Phase 31 pcap:

```bash
cd ~/aoip-lab
project3_ptp/scripts/derive_rtp_ptp_anchor_from_pcap.py \
  project1_packet_dump/captures/ptp-and-multicast-rtp-enp0s5-20260525-171752.pcap
```

The tool reads the first and last RTP packet for each configured stream and
prints:

```text
rtp_anchor
capture_anchor_s
media_span_ms
capture_span_ms
span_error_ms
first_playout_s
```

## Result

Test capture:

```text
project1_packet_dump/captures/ptp-and-multicast-rtp-enp0s5-20260525-171752.pcap
```

Observed:

```text
sample_rate = 48000 Hz
playout_latency_ms = 50
streams analyzed = 16
```

Example rows:

```text
stream-01 packets=1167 media_span_ms=1166.000 capture_span_ms=1165.928 span_error_ms=-0.072
stream-08 packets=734  media_span_ms=733.000  capture_span_ms=733.009  span_error_ms=0.009
stream-16 packets=189  media_span_ms=188.000  capture_span_ms=187.973  span_error_ms=-0.027
```

Meaning:

```text
RTP timestamp movement matches the expected 48 kHz media timeline.
The pcap-observed packet timing is close to the RTP media timing.
```

This is still a measurement of observed packet timing, not proof of real PTP
media-clock lock.

## Important Limitation

This lab tool uses pcap capture timestamps as the observable reference time.

That is useful for learning the timing math, but it is not the same as a
production AES67 sender whose RTP media clock is actually locked to PTP.

Current state:

```text
PTP traffic exists.
RTP traffic exists.
RTP timestamps are internally consistent.
The sender is not yet truly PTP-clocked.
```

## Meaning

This phase defines the bridge from packet transport to synchronized audio:

```text
RTP packet says which audio sample moment this is.
PTP clock says when that sample moment should happen globally.
Receiver latency gives the receiver time to buffer before playback.
```

This is the conceptual basis for playing 16 RTP streams as one aligned 128-channel
system.
