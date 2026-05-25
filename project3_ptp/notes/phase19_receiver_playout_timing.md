# Phase 19: Receiver Playout Timing

Phase 18 proved:

```text
RTP timestamp advances as media time
48 kHz + 1 ms packets = delta_ts 48
```

Phase 19 answers the next question:

```text
How does a receiver decide when to play a packet?
```

## The Bridge

A receiver needs an anchor.

Simple mental model:

```text
RTP timestamp R0 corresponds to PTP time T0
```

After that, every later packet can be scheduled:

```text
playout_time = T0 + ((rtp_timestamp - R0) / sample_rate) + receiver_latency
```

Baby version:

```text
R0 says "this is the starting sample position"
T0 says "this starting sample position belongs to this shared clock time"
receiver_latency gives the receiver enough buffer so packets can arrive before playback
```

## Example

Assume:

```text
sample_rate = 48000
packet_time = 1 ms
R0 = 0
T0 = 0 ms
receiver_latency = 50 ms
```

Then:

```text
packet 1: RTP timestamp 0   -> play at PTP time 50 ms
packet 2: RTP timestamp 48  -> play at PTP time 51 ms
packet 3: RTP timestamp 96  -> play at PTP time 52 ms
```

The receiver is not trying to play packets as soon as they arrive.

It is trying to play the right sample at the right shared time.

## SDP Clock Lines

RFC 7273 defines SDP signaling for RTP clock sources.

Two important lines are:

```text
a=ts-refclk:ptp=IEEE1588-2008:<grandmaster-clock-identity>:<domain>
a=mediaclk:direct=<offset>
```

Meaning:

```text
ts-refclk says which PTP clock is the reference clock
mediaclk says how the RTP media clock relates to that reference
```

Reference:

```text
https://datatracker.ietf.org/doc/html/rfc7273
```

For this VM, `pmc` showed:

```text
grandmasterIdentity 001c42.fffe.ee3f40
domainNumber        0
```

In SDP form, the clock identity is written as:

```text
00-1C-42-FF-FE-EE-3F-40
```

Example lines:

```text
a=ts-refclk:ptp=IEEE1588-2008:00-1C-42-FF-FE-EE-3F-40:0
a=mediaclk:direct=0
```

Important warning:

```text
These lines describe the clock relationship.
They do not magically make a sender hardware-locked to PTP.
```

Our VM still has software timestamping only, so this is a learning model, not a
production AES67 timing guarantee.

## Generate SDP With Clock Lines

Example:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./generate_sdp.py \
  --output-dir ../sdp/generated-ptp \
  --ptp-grandmaster 001c42.fffe.ee3f40 \
  --ptp-domain 0 \
  --mediaclk-direct 0
```

The generated SDP for stream 1 will include:

```text
a=ts-refclk:ptp=IEEE1588-2008:00-1C-42-FF-FE-EE-3F-40:0
a=mediaclk:direct=0
```

## Calculate Playout Schedule

Run:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./calculate_playout_schedule.py --count 5
```

Expected shape:

```text
packet rtp_timestamp media_elapsed_ms scheduled_playout_ptp_ms
000001             0            0.000                   50.000
000002            48            1.000                   51.000
000003            96            2.000                   52.000
```

This is not controlling real audio playback yet.

It is a calculator for the timing rule that a real receiver follows.

Observed output:

```text
Receiver playout schedule model
sample_rate:        48000 Hz
packet_time:        1 ms
samples_per_packet: 48
rtp_anchor:         0
ptp_anchor_ms:      0
playout_latency_ms: 50

packet rtp_timestamp media_elapsed_ms scheduled_playout_ptp_ms
000001             0            0.000                   50.000
000002            48            1.000                   51.000
000003            96            2.000                   52.000
000004           144            3.000                   53.000
000005           192            4.000                   54.000
```

Observed SDP clock lines:

```text
a=ts-refclk:ptp=IEEE1588-2008:00-1C-42-FF-FE-EE-3F-40:0
a=mediaclk:direct=0
```

## Why This Matters For 128 Channels

For 16 streams carrying 128 channels, each stream has its own RTP sequence
numbers and SSRC.

But synchronized playback requires the streams to agree on time:

```text
stream-01 timestamp timeline
stream-02 timestamp timeline
...
stream-16 timestamp timeline
all tied to the same PTP reference
```

That is the bridge from:

```text
16 RTP streams that carry audio
```

to:

```text
128 channels that play as one aligned audio system
```
