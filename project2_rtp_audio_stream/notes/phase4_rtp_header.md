# Phase 4: RTP Header

RTP is the small header in front of each audio payload.

For the current sender, every packet should look like:

```text
RTP header: 12 bytes
audio payload: PCM samples
```

Run the inspector:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./inspect_rtp_packets.py --group 127.0.0.1 --count 10
```

Then start the unicast sender in another terminal:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/sender
./send_rtp_audio.sh
```

Important fields:

- `version`: should be `2`. RTP version 2 is the normal RTP version.
- `pt`: payload type. Our sender uses `96`.
- `seq`: sequence number. It should increase by 1 each packet.
- `timestamp`: media clock timestamp. For 48 kHz audio, this advances according to how many audio samples are in the packet.
- `payload_bytes`: how much audio data is inside this packet.
- `ssrc`: stream identifier chosen by the sender.

For same-machine learning, start with unicast. Multicast adds interface and VM
network behavior. The multicast sender sets `loop=true`, but some VM network
modes still need extra investigation before local multicast receivers see the
stream.

Why this matters for AES67:

- packet loss is detected by sequence gaps.
- timing is reconstructed from RTP timestamps.
- SDP maps payload type `96` to `L16/48000/1`.
- packet time can be checked from timestamp deltas.
