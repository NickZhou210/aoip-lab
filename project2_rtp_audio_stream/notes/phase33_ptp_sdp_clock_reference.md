# Phase 33: SDP PTP Clock Reference

Phase 32 explained the RTP-to-reference-time anchor.

Phase 33 writes that timing reference into SDP so a receiver can know which PTP
clock the RTP media clock claims to reference.

## Important SDP Lines

For the current VM Grandmaster:

```text
grandmasterIdentity = 001c42.fffe.ee3f40
SDP clock identity = 00-1C-42-FF-FE-EE-3F-40
PTP domain = 0
```

Each generated SDP should include:

```text
a=ts-refclk:ptp=IEEE1588-2008:00-1C-42-FF-FE-EE-3F-40:0
a=mediaclk:direct=0
```

Meaning:

```text
ts-refclk says which PTP Grandmaster/domain is the reference clock.
mediaclk says how the RTP media clock is related to that reference.
```

## Generate PTP-Aware SDP Files

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./generate_sdp.py \
  --output-dir ../sdp/generated-ptp \
  --ptp-grandmaster 001c42.fffe.ee3f40 \
  --ptp-domain 0 \
  --mediaclk-direct 0
```

## Validate The Generated SDP Files

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./validate_sdp_clock_lines.py \
  --sdp-dir ../sdp/generated-ptp \
  --ptp-grandmaster 001c42.fffe.ee3f40 \
  --ptp-domain 0 \
  --mediaclk-direct 0
```

Expected result:

```text
PASS: 16 SDP files contain expected RTP and PTP clock reference lines
```

## Result

Generated:

```text
project2_rtp_audio_stream/sdp/generated-ptp/stream-01.sdp
...
project2_rtp_audio_stream/sdp/generated-ptp/stream-16.sdp
```

Example from stream 1:

```text
c=IN IP4 239.69.1.1/32
m=audio 5004 RTP/AVP 96
a=rtpmap:96 L16/48000/8
a=ptime:1
a=recvonly
a=ts-refclk:ptp=IEEE1588-2008:00-1C-42-FF-FE-EE-3F-40:0
a=mediaclk:direct=0
a=x-aoip-channel-range:1-8
```

Validation:

```text
PASS: 16 SDP files contain expected RTP and PTP clock reference lines
```

## Boundary

These SDP lines are signaling.

They do not automatically make the sender PTP-locked. They tell a receiver what
clock relationship the stream is supposed to use. The actual media clock still
needs to be disciplined by PTP in a production AES67 implementation.
