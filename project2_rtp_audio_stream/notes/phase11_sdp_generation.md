# Phase 11: SDP Generation

SDP is the description of an RTP stream.

RTP packets contain payload type `96`, but `96` alone does not say what audio
format it is. SDP explains it:

```text
a=rtpmap:96 L16/48000/8
```

For the 128-channel plan, each 8-channel RTP stream gets one SDP file:

```text
stream-01.sdp
stream-02.sdp
...
stream-16.sdp
```

Generate them:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./generate_sdp.py
```

Example for stream 1:

```text
c=IN IP4 239.69.1.1/32
m=audio 5004 RTP/AVP 96
a=rtpmap:96 L16/48000/8
a=ptime:1
a=x-aoip-channel-range:1-8
```

Meaning:

- `239.69.1.1`: multicast group.
- `5004`: RTP/UDP port.
- `96`: RTP payload type.
- `L16/48000/8`: 16-bit PCM, 48 kHz, 8 channels.
- `ptime:1`: 1 ms per packet.
- `x-aoip-channel-range`: lab metadata for our channel mapping.

The `x-aoip-channel-range` line is not a core AES67 requirement. It is a lab
helper so humans can see which global channels this stream carries.

