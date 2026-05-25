# Phase 7: Bandwidth And MTU

Before 128 channels, calculate the packet sizes.

The simple formula is:

```text
payload_bytes = samples_per_packet * bytes_per_sample * channels
```

For 48 kHz and 1 ms:

```text
samples_per_packet = 48000 * 0.001 = 48
```

For L16:

```text
bytes_per_sample = 2
```

So:

```text
1ch   = 48 * 2 * 1   = 96 bytes
2ch   = 48 * 2 * 2   = 192 bytes
8ch   = 48 * 2 * 8   = 768 bytes
16ch  = 48 * 2 * 16  = 1536 bytes
128ch = 48 * 2 * 128 = 12288 bytes
```

Normal Ethernet MTU is usually 1500 bytes. That does not mean the audio payload
can use all 1500 bytes, because RTP, UDP, and IP headers also need space:

```text
RTP header = 12 bytes
UDP header = 8 bytes
IPv4 header = 20 bytes
total = 40 bytes
```

So a 1500-byte MTU leaves about:

```text
1500 - 40 = 1460 payload bytes
```

This means:

```text
16ch L16 at 1 ms = 1536 payload bytes
```

already does not fit into one normal MTU packet.

Run the calculator:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./calc_stream.py --channels 2
./calc_stream.py --channels 8
./calc_stream.py --channels 128
./calc_stream.py --bits 24 --channels 128
```

Learning target:

- 2ch is easy.
- 8ch still fits in one packet.
- 16ch L16 at 1 ms is already too large for normal MTU.
- 128ch must be split, use larger MTU, use different packet time, or use multiple streams.

