# Phase 3: SDP

SDP means Session Description Protocol. It is not the audio. It is the label on the audio stream.

RTP packets only contain numbers and payload bytes. A receiver still needs to know:

- which multicast group to join
- which UDP port to listen on
- which payload type means which codec
- sample rate
- channel count
- packet time

The file `../sdp/rtp-l16-mono.sdp` describes the multicast stream created by:

```bash
../sender/send_multicast_rtp_audio.sh
```

Important lines:

```text
c=IN IP4 239.69.1.1/32
m=audio 5004 RTP/AVP 96
a=rtpmap:96 L16/48000/1
a=ptime:1
```

Meaning:

- `239.69.1.1`: multicast group.
- `5004`: UDP/RTP port.
- `96`: RTP dynamic payload type.
- `L16/48000/1`: 16-bit linear PCM, 48 kHz, 1 channel.
- `ptime:1`: 1 ms of audio per packet.

In full AES67, SDP is how other software or hardware understands your stream before receiving it.

