# Phase 30: Multicast RTP Packet Capture

This phase verifies the 16 configured RTP streams at the network packet level.

Phase 29 proved that the sender and monitor programs can exchange all 16
streams. Phase 30 checks the packets captured on the VM network interface.

## One-Command Test

Run this from an interactive Ubuntu terminal because `tcpdump` needs `sudo`:

```bash
cd ~/aoip-lab
project1_packet_dump/scripts/run_multicast_rtp_capture_test.sh enp0s5 10.211.55.6 8
```

Do not run this specific command through a non-interactive SSH command, because
`sudo` needs a terminal to ask for your password.

This command:

```text
starts tcpdump capture on enp0s5
runs the 16-stream multicast RTP sender/monitor test
waits for the capture to finish
summarizes the captured pcap
```

## Manual Capture Command

Start the capture before running the senders:

```bash
cd ~/aoip-lab
project1_packet_dump/scripts/capture_multicast_rtp_16.sh enp0s5 8
```

In another terminal, generate the traffic:

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

Then summarize the capture:

```bash
cd ~/aoip-lab
project1_packet_dump/scripts/summarize_multicast_rtp_capture.py \
  project1_packet_dump/captures/<capture-file>.pcap
```

## Expected Packet Shape

Each configured stream should appear as:

```text
destination IP = 239.69.1.x
destination UDP port = 5004, 5006, ... 5034
UDP payload bytes = 780
RTP header bytes = 12
RTP audio payload bytes = 768
RTP payload type = 96
RTP timestamp step = 48
```

The `780` byte UDP payload contains:

```text
12 bytes RTP header + 768 bytes L16 audio payload
```

This is different from the approximate `808` byte IP packet size in
`streams.json`, which includes IP and UDP headers:

```text
20 bytes IPv4 header + 8 bytes UDP header + 780 bytes UDP payload = 808 bytes
```

## Result

Test capture:

```text
capture: project1_packet_dump/captures/multicast-rtp-enp0s5-20260525-170823.pcap
size: 8.8M
tcpdump packets captured: 10898
tcpdump packets received by filter: 10898
tcpdump packets dropped by kernel: 0
configured RTP packets parsed: 10898
source IP: 10.211.55.6
```

Summary:

```text
PASS: 16 configured multicast RTP streams found
UDP payload bytes = 780
RTP audio payload bytes = 768
RTP payload type = 96
sequence breaks = 0
timestamp breaks = 0
```

The per-stream packet counts decrease from stream 1 to stream 16 because the
senders start one after another while the capture window is fixed. That does not
indicate packet loss. The important checks are that all 16 groups are present,
all payload sizes match, and there are no sequence or timestamp breaks.

## Meaning

If the capture summary passes, the VM is producing the intended multicast RTP
packet set on `enp0s5`.

This still does not prove:

```text
another physical receiver can receive the streams
IGMP snooping behavior is correct on a real switch
the RTP streams are locked to a real PTP clock
```
