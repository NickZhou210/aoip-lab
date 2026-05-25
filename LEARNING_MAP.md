# AOIP / AES67 Learning Map

This project is not only code. It is a ladder for learning how audio over IP becomes AES67.

## Big Picture

AoIP means audio is moved as network packets instead of analog voltage or a local sound-card stream.

The learning stack is:

```text
Audio samples
-> PCM format
-> RTP payload
-> UDP packet
-> IP unicast or multicast
-> Ethernet
-> clock synchronization
-> discovery/session description
```

AES67 is a strict profile of that stack. It does not invent a new transport. It says which existing pieces must be used, and how tightly they must behave.

## Where The Current Project Is

```text
project1_packet_dump
  packet observation layer
  tcpdump sees what is actually on the network

project2_rtp_audio_stream
  RTP audio experiment layer
  GStreamer creates and receives L16 RTP audio
```

You have already proven this chain:

```text
test tone
-> 48 kHz mono PCM
-> RTP L16 payload
-> UDP 127.0.0.1:5004
-> RTP depayload
-> WAV file
```

That is Phase 1. It is not full AES67 yet, but it is the correct foundation.

## Script Logic

### `send_rtp_audio.sh`

This is the local RTP sender.

```text
audiotestsrc
-> audio/x-raw,format=S16BE,rate=48000,channels=1
-> rtpL16pay pt=96
-> udpsink host=127.0.0.1 port=5004
```

Meaning:

- `audiotestsrc`: makes a synthetic sine wave.
- `S16BE`: 16-bit signed PCM, big-endian. RTP L16 uses network byte order, which is big-endian.
- `rate=48000`: AES67 commonly uses 48 kHz.
- `channels=1`: one audio channel for now.
- `rtpL16pay`: wraps PCM samples into RTP packets.
- `pt=96`: dynamic RTP payload type. SDP will explain that 96 means L16/48000/1.
- `udpsink`: sends the RTP packets over UDP.

### `receive_rtp_audio.sh`

This is the local RTP receiver.

```text
udpsrc
-> rtpjitterbuffer
-> rtpL16depay
-> audioconvert
-> wavenc
-> filesink
```

Meaning:

- `udpsrc`: listens for UDP packets.
- `caps`: tells GStreamer how to interpret those UDP packets as RTP audio.
- `rtpjitterbuffer`: smooths timing variation.
- `rtpL16depay`: removes the RTP wrapper and recovers PCM.
- `wavenc`: writes the PCM samples as a WAV file.

### Multicast Scripts

The multicast scripts use:

```text
239.69.1.1:5004
```

Unicast sends to one specific host. Multicast sends to a group address, and receivers join that group. Real AES67 systems usually use multicast for shared audio streams.

## The Important Numbers

### Sample Rate

```text
48000 samples/second
```

At 48 kHz, one channel produces 48,000 samples every second.

### Bit Depth

```text
L16 = 16 bits/sample = 2 bytes/sample
L24 = 24 bits/sample = 3 bytes/sample
```

AES67 commonly uses L16 or L24.

### Channels

For mono L16:

```text
48000 samples/s * 2 bytes = 96000 bytes/s
```

For 128-channel L24:

```text
48000 samples/s * 3 bytes * 128 channels = 18,432,000 bytes/s
```

That is about 147.5 Mbit/s before RTP/UDP/IP/Ethernet overhead.

### Packet Time

Packet time is how much audio each RTP packet carries.

For 1 ms at 48 kHz:

```text
48 samples/channel/packet
```

For mono L16:

```text
48 samples * 2 bytes = 96 bytes payload per packet
```

For 128-channel L24:

```text
48 samples * 3 bytes * 128 = 18432 bytes payload per packet
```

That is too large for a normal 1500-byte Ethernet MTU. This is why high channel counts need careful packetization, multiple streams, jumbo frames, or vendor-specific design choices.

## Why 128 Channels Is Not Just "Change channels=128"

The jump from 1 channel to 128 channels changes:

- payload size
- packet size
- bandwidth
- receiver buffering
- CPU load
- switch behavior
- multicast planning
- interoperability expectations

We will climb toward 128 channels in stages:

1. 1 channel L16 local loopback.
2. 1 channel L16 multicast.
3. 2 channel L16 multicast with SDP.
4. 8 channel L16 or L24.
5. Bandwidth calculation and packet-size verification.
6. PTP synchronization.
7. 128-channel architecture decision.

## What Full AES67 Adds Later

The current project has RTP audio. Full AES67 still needs:

- SDP: a text description of the stream.
- PTP: shared clock synchronization.
- correct packet time.
- multicast behavior across real network interfaces.
- receiver compatibility with other AES67 devices/software.
- clear channel mapping.

## Next Practical Skill: Reading RTP Headers

After multicast works, inspect the RTP header itself:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./inspect_rtp_packets.py --group 127.0.0.1 --count 10
```

Then start:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/sender
./send_rtp_audio.sh
```

Use unicast for the first RTP header lesson because it removes multicast
interface behavior from the experiment. After the RTP fields make sense, return
to multicast and debug it as a network-layer problem.

The key learning is:

```text
sequence number = packet order
timestamp = audio time
payload type = codec mapping
SSRC = stream identity
payload bytes = audio carried in that packet
```

For the current 1 ms mono L16 sender, the expected values are:

```text
delta_seq = 1
delta_ts = 48
payload_bytes = 96
```

That comes from:

```text
48000 samples/second * 0.001 second = 48 samples/packet
48 samples * 2 bytes/sample * 1 channel = 96 bytes/packet
```
