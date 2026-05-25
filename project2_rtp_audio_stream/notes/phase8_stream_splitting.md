# Phase 8: Stream Splitting

128 channels should not be packed into one normal RTP packet stream at 1 ms.

For L16, 48 kHz, 1 ms:

```text
1 channel = 96 payload bytes
128 channels = 12288 payload bytes
```

Normal MTU leaves about:

```text
1460 payload bytes
```

So 128 channels must be split.

A simple first design:

```text
128 channels = 16 RTP streams * 8 channels each
```

Each 8-channel stream:

```text
48 samples * 2 bytes * 8 channels = 768 payload bytes
768 + 40 RTP/UDP/IP bytes = 808 IP packet bytes
```

That fits a normal 1500-byte MTU.

Run:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./plan_streams.py --total-channels 128 --channels-per-stream 8
```

The plan gives each stream:

- multicast group
- UDP port
- channel range
- payload size
- IP packet size
- MTU safety

This is architecture work. It answers:

```text
which channels go into which RTP stream?
where does each stream go on the network?
does each packet fit?
```

