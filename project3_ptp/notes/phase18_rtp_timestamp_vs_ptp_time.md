# Phase 18: RTP Timestamp Versus PTP Time

This phase connects the RTP work to the PTP work.

Simple mental model:

```text
PTP time       = what time is it?
RTP timestamp  = which audio sample time is this packet carrying?
SDP            = how should the receiver interpret this stream?
```

## The Most Important Distinction

PTP and RTP timestamp are not the same number.

PTP is a shared wall clock.

RTP timestamp is a media clock counter.

For our current audio:

```text
sample rate = 48000 Hz
packet time = 1 ms
samples per packet = 48
```

Therefore every RTP packet should move forward by:

```text
delta_ts = 48
```

That is true for 1 channel, 2 channels, 8 channels, or 128 channels.

Why?

Because RTP timestamp counts sample time, not bytes.

## Byte Size Changes, Time Step Does Not

For 1 ms of L16 audio:

```text
1ch: 48 samples * 2 bytes * 1 channel = 96 bytes
2ch: 48 samples * 2 bytes * 2 channels = 192 bytes
8ch: 48 samples * 2 bytes * 8 channels = 768 bytes
```

But the RTP timestamp step is still:

```text
48 samples of time
```

So:

```text
channels change payload_bytes
packet time changes delta_ts
sample rate changes timestamp units
```

## Where PTP Enters AES67

RTP alone can say:

```text
this packet carries audio sample time N
the next packet carries audio sample time N + 48
```

But RTP alone does not tell every device in the network:

```text
play sample time N at exactly this shared real-world time
```

That is why AES67 needs PTP.

PTP gives devices a common clock. RTP timestamps give audio a sample timeline.
An AES67 receiver uses both:

```text
PTP shared clock
+ RTP timestamp sequence
+ SDP stream description
+ receiver buffer
= synchronized playback
```

## What Our Current GStreamer Sender Does

Our current sender creates a valid RTP timestamp sequence:

```text
delta_ts = 48
```

But it is not yet locked to a real PTP hardware clock.

Baby version:

```text
The packets have a neat audio timeline.
But the timeline is not yet nailed to a professional shared clock.
```

This is fine for the learning lab. It is not yet the final AES67 timing model.

## Observe RTP Timestamp Clock

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

Expected result:

```text
delta_ts = 48
rtp_elapsed_ms grows by 1.000 ms per packet
payload_bytes = 768 for stream-01 because it is 8ch L16
```

The local arrival time may wobble slightly because Linux scheduling, VM timing,
and socket delivery are not perfect.

## What The Observation Script Does

It receives RTP packets and prints:

```text
idx
seq
delta_ts
rtp_elapsed_ms
arrival_elapsed_ms
arrival_minus_rtp_ms
payload_bytes
```

Meaning:

- `idx`: packet count printed by this tool.
- `seq`: RTP sequence number from the packet.
- `delta_ts`: RTP timestamp step since the previous packet.
- `rtp_elapsed_ms`: audio time elapsed according to RTP timestamp.
- `arrival_elapsed_ms`: local receive time elapsed according to this computer.
- `arrival_minus_rtp_ms`: how far packet arrival timing differs from RTP media timing.
- `payload_bytes`: audio bytes inside the RTP packet.

## What This Proves

This phase proves:

```text
RTP timestamp is a 48 kHz media clock
1 ms packets advance by 48 timestamp ticks
8-channel payload size is larger, but timestamp step stays 48
```

This phase does not prove:

```text
the sender is locked to PTP
the receiver can align playback to PTP time
hardware AES67 timing accuracy
```

That missing bridge is the next topic.

## Observed Result On This VM

Test command:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./observe_rtp_timestamp_clock.py --group 127.0.0.1 --port 5004 --count 20
```

Sender:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./send_stream_from_config.py --stream 1 --host 127.0.0.1
```

Observed sample:

```text
idx seq delta_ts rtp_elapsed_ms arrival_elapsed_ms arrival_minus_rtp_ms payload_bytes
001 19787        0          0.000              0.000                0.000   768
002 19788       48          1.000              0.118               -0.882   768
003 19789       48          2.000              1.183               -0.817   768
004 19790       48          3.000              2.257               -0.743   768
...
020 19806       48         19.000             18.216               -0.784   768
```

Confirmed:

```text
delta_ts = 48
payload_bytes = 768
rtp_elapsed_ms advances by 1 ms per packet
```

Why `arrival_elapsed_ms` is not exactly the same as `rtp_elapsed_ms`:

```text
RTP timestamp describes the sender media timeline
arrival time describes when this VM process received the UDP packet
```

Those are related, but they are not identical. Linux scheduling, VM timing,
socket buffering, and GStreamer startup can all move arrival time slightly.

The key learning is:

```text
RTP timestamp is clean media time
packet arrival time is network/computer delivery time
PTP is the shared reference used later to align media time to real playback time
```
