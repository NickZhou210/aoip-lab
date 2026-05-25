# Phase 31: PTP and RTP in One Capture

This phase captures the two traffic classes an AES67 network needs:

```text
PTP clock traffic: UDP 319 and UDP 320
RTP audio traffic: multicast UDP 5004 through 5034
```

## One-Command Test

Run this from an interactive Ubuntu terminal because `tcpdump` and `ptp4l` need
`sudo`:

```bash
cd ~/aoip-lab
project1_packet_dump/scripts/run_ptp_rtp_capture_test.sh enp0s5 10.211.55.6 12
```

The script does this:

```text
starts temporary ptp4l if ptp4l is not already running
starts tcpdump with a PTP + multicast RTP filter
runs the 16-stream multicast RTP sender/monitor test
summarizes PTP packets from the same pcap
summarizes RTP packets from the same pcap
stops temporary ptp4l if the script started it
```

## Expected PTP Result

The PTP summary should show packets on:

```text
UDP 319: PTP event messages
UDP 320: PTP general messages
```

Because the VM is alone on this PTP domain, it may still be its own Grandmaster.
That is acceptable for this phase. The point here is packet coexistence, not yet
accurate clock discipline.

## Expected RTP Result

The RTP summary should still show:

```text
PASS: 16 configured multicast RTP streams found
UDP payload bytes = 780
RTP audio payload bytes = 768
RTP payload type = 96
sequence breaks = 0
timestamp breaks = 0
```

## Meaning

If both summaries pass, the lab has produced one capture containing:

```text
PTP timing plane
RTP media plane
```

This is closer to a real AES67 network than testing RTP and PTP separately.

This still does not prove:

```text
the RTP sender is clock-locked to PTP
the receiver schedules playback from PTP timestamps
multiple devices agree on one Grandmaster
```
