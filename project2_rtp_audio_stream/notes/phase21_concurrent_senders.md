# Phase 21: Concurrent 16-Stream Sender Test

The 128-channel plan is:

```text
16 RTP streams * 8 channels per stream = 128 channels
```

Before testing receivers, multicast, or external AES67 devices, we need a basic
sender-side test:

```text
Can the VM start all 16 RTP senders at the same time?
```

## What This Tests

This phase tests:

```text
16 GStreamer sender pipelines can run concurrently
each stream uses its configured UDP port
each stream uses 8-channel L16 audio
the sender process manager can stop all pipelines cleanly
```

This phase does not test:

```text
receiver synchronization
multicast switch behavior
PTP-locked media clock generation
external AES67 compatibility
```

## Run Command

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_concurrent_senders.py --duration 5
```

Default behavior:

```text
host = 127.0.0.1
duration = 5 seconds
streams = all 16 streams from streams.json
```

Logs are written under:

```text
project2_rtp_audio_stream/logs/
```

The logs are local test artifacts and are ignored by Git.

## Why Local Unicast First

This test intentionally uses:

```text
127.0.0.1
```

Reason:

```text
local unicast removes multicast and VM network behavior
```

That keeps this phase focused on sender concurrency.

Multicast is a separate test phase.

## Expected Stream Layout

```text
stream-01 -> 127.0.0.1:5004  channels 1-8
stream-02 -> 127.0.0.1:5006  channels 9-16
...
stream-16 -> 127.0.0.1:5034  channels 121-128
```

Each stream should still use:

```text
L16
48 kHz
1 ms packet time
768 audio payload bytes per RTP packet
```

## Success Condition

Expected final line:

```text
PASS: 16 senders ran concurrently
```

Meaning:

```text
the sender side can generate all 16 configured RTP streams at the same time
```

This is a necessary step toward 128 channels, but it is not sufficient for full
AES67.

## Observed Result On Ubuntu

Command:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_concurrent_senders.py --duration 2 --startup-delay 0.02
```

Observed:

```text
started_count: 16
PASS: 16 senders ran concurrently
```

The latest log directory contained 16 sender logs.

Example stream-01 log confirmed:

```text
Destination: 127.0.0.1:5004
Channels: 1-8 (8ch)
Format: L16/48000
Packet time: 1.0 ms
Expected payload bytes: 768
```

After stopping, process cleanup check showed:

```text
gst_count=0
sender_count=0
```

Meaning:

```text
all 16 senders started
all 16 sender logs were created
no GStreamer sender process was left running
```
