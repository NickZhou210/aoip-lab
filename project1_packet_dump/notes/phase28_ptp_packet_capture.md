# Phase 28: PTP Packet Capture Helper

This phase standardizes PTP packet capture for the lab.

## Why This Exists

We already know how to use tcpdump and Wireshark.

The purpose here is different:

```text
create a repeatable project command for PTP baseline captures
```

This gives us a local reference when comparing against:

```text
Yamaha AES67 mode
Dante AES67 mode
Ravenna tools
other AES67 devices
```

## PTP Ports

PTP over UDP uses:

```text
UDP 319 = event messages
UDP 320 = general messages
```

Common message types include:

```text
Announce
Sync
Follow_Up
Delay_Req
Delay_Resp
```

## Capture Command

Start `ptp4l` in one terminal:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./run_ptp4l_software.sh enp0s5
```

Capture PTP in another terminal:

```bash
cd ~/aoip-lab/project1_packet_dump/scripts
./capture_ptp.sh enp0s5 10
```

Arguments:

```text
argument 1 = interface
argument 2 = duration in seconds
argument 3 = optional output pcap path
```

Default output:

```text
project1_packet_dump/captures/ptp-<iface>-<timestamp>.pcap
```

## Live Monitor

```bash
cd ~/aoip-lab/project1_packet_dump/scripts
./live_ptp_monitor.sh enp0s5
```

Stop with:

```text
Ctrl+C
```

## Inspect A Capture

```bash
cd ~/aoip-lab/project1_packet_dump/scripts
./inspect_ptp_capture.sh ../captures/<file>.pcap
```

This prints the first packets with tcpdump.

## What To Check

For the current VM-only PTP master test:

```text
source IP should include 10.211.55.6
UDP 319/320 packets should appear
traffic should be visible while ptp4l is running
```

This does not prove hardware timestamp quality.

It proves:

```text
ptp4l is emitting PTP traffic on the selected interface
the project can save a reproducible PTP pcap for comparison
```
