# Phase 5: Packet Time

Packet time means how much audio duration each RTP packet carries.

For this lab:

```text
sample rate = 48000 samples/second
packet time = 1 ms
channels = 1
format = L16 = 2 bytes/sample
```

So one packet carries:

```text
48000 samples/second * 0.001 second = 48 samples
48 samples * 2 bytes * 1 channel = 96 payload bytes
```

The RTP timestamp also moves by the number of samples:

```text
delta_ts = 48
```

That is why a correct 1 ms mono L16 stream should look like:

```text
delta_seq = 1
delta_ts = 48
payload_bytes = 96
```

The sender forces this with:

```text
min-ptime=1000000
max-ptime=1000000
ptime-multiple=1000000
```

GStreamer uses nanoseconds for these values:

```text
1 ms = 1,000,000 ns
```

Why this matters for AES67:

- smaller packet time means lower latency.
- smaller packet time means more packets per second.
- more packets per second means more packet overhead.
- timestamp deltas must match the audio duration in each packet.
- SDP `a=ptime:1` should match what the sender actually does.

For 128-channel planning, packet time becomes a design constraint, not a small detail.

