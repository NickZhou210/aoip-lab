# Phase 20: Multi-Stream PTP Alignment

The 128-channel design currently uses:

```text
128 channels = 16 RTP streams * 8 channels per stream
```

This phase asks:

```text
How do 16 RTP streams play as one aligned 128-channel system?
```

## The Wrong Mental Model

The wrong model is:

```text
if 16 UDP packets arrive at the same time, the audio is aligned
```

That is not how AES67 synchronization should be understood.

Packets can arrive with small timing differences because of:

```text
sender scheduling
network switch buffering
VM scheduling
receiver socket delivery
jitter buffer behavior
```

Arrival time is not the master truth.

## The Correct Mental Model

The better model is:

```text
each stream has an RTP media timeline
all timelines reference the same PTP clock
the receiver schedules playback from RTP timestamp plus PTP reference
```

The same Phase 19 rule applies:

```text
playout_time = PTP_anchor + RTP_media_elapsed + receiver_latency
```

For aligned 16-stream playback, equivalent audio sample moments across streams
must map to the same `playout_time`.

## What Must Match

For each stream:

```text
sample_rate = 48000
packet_time = 1 ms
samples_per_packet = 48
PTP reference = same grandmaster/domain
receiver latency = same playback policy
```

Then stream alignment depends on the RTP media timeline mapping.

Simple case:

```text
stream-01 packet N timestamp 4800 -> play at 150 ms
stream-02 packet N timestamp 4800 -> play at 150 ms
stream-03 packet N timestamp 4800 -> play at 150 ms
```

Those streams are aligned for that sample moment.

Skewed case:

```text
stream-01 packet N timestamp 4800 -> play at 150 ms
stream-02 packet N timestamp 4848 -> play at 151 ms
```

Stream 2 is one packet, or 1 ms, late in the media timeline.

## Calculate Alignment

Run:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./calculate_multistream_alignment.py --packet-index 100
```

Expected result:

```text
alignment_result: aligned
```

This means all 16 streams map packet index 100 to the same scheduled PTP
playout time.

Observed result:

```text
stream-01 1-8               4800          100.000                  150.000                    0.000
stream-02 9-16              4800          100.000                  150.000                    0.000
...
stream-16 121-128           4800          100.000                  150.000                    0.000

max_alignment_offset_ms: 0.000
alignment_result:        aligned
```

## Demonstrate A Bad Offset

Run:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./calculate_multistream_alignment.py --packet-index 100 --skew-stream 2 --skew-samples 48
```

Expected result:

```text
stream-02 offset_from_stream_01_ms = 1.000
alignment_result: not aligned
```

Observed result:

```text
stream-01 1-8               4800          100.000                  150.000                    0.000
stream-02 9-16              4848          101.000                  151.000                    1.000
stream-03 17-24             4800          100.000                  150.000                    0.000
...

max_alignment_offset_ms: 1.000
alignment_result:        not aligned
```

Meaning:

```text
stream-02 is one 48 kHz audio packet ahead of stream-01
48 samples / 48000 samples per second = 1 ms
```

## Why This Matters

For 128 channels, the receiver must not treat the 16 streams as unrelated audio.

It needs to reconstruct this:

```text
stream-01 channels 1-8
stream-02 channels 9-16
...
stream-16 channels 121-128
```

as one shared time structure:

```text
sample time X on channel 1
sample time X on channel 64
sample time X on channel 128
all play at the same PTP time
```

That is the conceptual jump from:

```text
many RTP streams
```

to:

```text
one synchronized 128-channel AoIP system
```
