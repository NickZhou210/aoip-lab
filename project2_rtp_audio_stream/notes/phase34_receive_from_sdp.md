# Phase 34: Receiver From SDP

Phase 33 generated SDP files with PTP clock reference lines.

Phase 34 makes SDP part of the receiver workflow.

Instead of reading `streams.json`, the receiver can read one SDP file and derive:

```text
multicast group
UDP port
RTP payload type
encoding
sample rate
channel count
packet time
PTP clock reference
media clock relationship
```

## Dry Run

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./receive_stream_from_sdp.py ../sdp/generated-ptp/stream-01.sdp --dry-run
```

Expected parsed fields:

```text
Group:         239.69.1.1
Port:          5004
Format:        L16/48000/8
Payload type:  96
Packet time:   1 ms
ts-refclk:     a=ts-refclk:ptp=IEEE1588-2008:00-1C-42-FF-FE-EE-3F-40:0
mediaclk:      a=mediaclk:direct=0
```

Expected GStreamer command shape:

```text
udpsrc multicast-group=239.69.1.1 multicast-iface=enp0s5 auto-multicast=true port=5004
caps=application/x-rtp,media=audio,encoding-name=L16,clock-rate=48000,channels=8,payload=96
rtpjitterbuffer latency=50
rtpL16depay
wavenc
filesink location=...
```

## Result

Verified on Ubuntu with:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./receive_stream_from_sdp.py ../sdp/generated-ptp/stream-01.sdp --dry-run
```

Observed:

```text
Group:         239.69.1.1
Port:          5004
Format:        L16/48000/8
Payload type:  96
Packet time:   1 ms
Direction:     recvonly
Channel range: 1-8
ts-refclk:     a=ts-refclk:ptp=IEEE1588-2008:00-1C-42-FF-FE-EE-3F-40:0
mediaclk:      a=mediaclk:direct=0
```

The generated receiver command used:

```text
udpsrc multicast-group=239.69.1.1 multicast-iface=enp0s5 auto-multicast=true port=5004
caps=application/x-rtp,media=audio,encoding-name=L16,clock-rate=48000,channels=8,payload=96
```

## Meaning

This is the receiver-side meaning of SDP:

```text
SDP is not audio.
SDP describes how to receive and interpret the RTP audio.
```

This phase does not yet prove synchronized playback. It proves that the receiver
can consume the same SDP fields that AES67 receivers need before joining a
stream.
