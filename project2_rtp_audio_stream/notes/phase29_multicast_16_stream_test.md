# Phase 29: Multicast 16-Stream RTP Test

This phase moves the 16-stream RTP test from local unicast to multicast.

Previous local test:

```text
127.0.0.1
```

Multicast test:

```text
stream-01 -> 239.69.1.1:5004
stream-02 -> 239.69.1.2:5006
...
stream-16 -> 239.69.1.16:5034
```

## Why This Matters

Real AES67 deployments commonly use multicast for shared streams.

This phase checks whether the VM can:

```text
send all configured multicast RTP streams
join all configured multicast groups
observe RTP headers from all streams
```

## Run Command

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_concurrent_sender_monitor.py \
  --use-config-groups \
  --iface enp0s5 \
  --iface-ip 10.211.55.6 \
  --count 20 \
  --sender-duration 6 \
  --monitor-timeout 5
```

## Expected Result

Each stream should show:

```text
packets = 20
payload_bytes = 768
delta_seq = 1
delta_ts = 48
status = PASS
```

Expected final line:

```text
PASS: 16 streams reached 20 packets
```

## Result

Tested on the Ubuntu VM interface:

```text
interface: enp0s5
interface_ip: 10.211.55.6
streams: 16
total_channels: 128
groups: 239.69.1.1 through 239.69.1.16
ports: 5004 through 5034
```

Observed result:

```text
PASS: 16 streams reached 20 packets
payload_bytes = 768
delta_seq = 1
delta_ts = 48
```

No leftover sender or GStreamer processes were running after the test.

## What This Does Not Prove

This still does not prove:

```text
external switch multicast behavior
IGMP snooping behavior on real hardware
receiver playback synchronization
PTP-locked media clock generation
```

It proves the current VM can send and locally observe the configured multicast
RTP stream set.
