# Phase 22: Monitor All 16 RTP Streams

Phase 21 proved:

```text
16 sender processes can run concurrently
```

Phase 22 checks the actual RTP packets from every stream.

## What This Tests

For each configured stream, the monitor checks:

```text
packet_count reaches target count
payload_bytes = 768
delta_seq = 1
delta_ts = 48
payload_type = 96
RTP version = 2
SSRC is stable within the stream
```

This confirms that all 16 senders are producing the expected RTP header pattern.

## Run Command

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_concurrent_sender_monitor.py --count 20
```

This wrapper:

```text
starts all 16 senders
waits briefly
monitors all 16 UDP ports
stops the senders
```

## Direct Monitor Command

If senders are already running:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./monitor_all_streams.py --host 127.0.0.1 --count 20
```

## Expected Result

Expected final line:

```text
PASS: 16 streams reached 20 packets
```

Each stream should show:

```text
packets = 20
payload_bytes = 768
delta_seq = 1
delta_ts = 48
status = PASS
```

## What This Does Not Prove

This phase still does not prove:

```text
receiver playback synchronization
multicast network delivery
PTP-locked sender timing
external AES67 interoperability
```

It proves the configured 128-channel RTP sender set is producing the expected
packet structure on all 16 streams.

## Observed Result On Ubuntu

Command:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_concurrent_sender_monitor.py --count 20 --sender-duration 6 --monitor-timeout 5
```

Observed:

```text
stream packets payload_bytes delta_seq delta_ts ssrcs status
stream-01      20 768           1         48       0x833405bd           PASS
stream-02      20 768           1         48       0x91647b3a           PASS
stream-03      20 768           1         48       0xe1bd1fb2           PASS
...
stream-16      20 768           1         48       0x8eafed79           PASS

PASS: 16 streams reached 20 packets
```

Cleanup check:

```text
gst_count=0
sender_count=0
```

Meaning:

```text
all 16 streams emitted valid RTP packets
each stream had the expected 8-channel payload size
each stream advanced by one sequence number per packet
each stream advanced by 48 RTP timestamp ticks per packet
```
