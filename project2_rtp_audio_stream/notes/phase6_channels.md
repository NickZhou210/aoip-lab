# Phase 6: Channels

Channels means how many parallel audio signals are carried in the stream.

Mono:

```text
channels = 1
```

Stereo:

```text
channels = 2
```

For 1 ms packet time at 48 kHz:

```text
samples per channel per packet = 48
```

The RTP timestamp is based on sample time, not total bytes.

So both 1 channel and 2 channels still have:

```text
delta_ts = 48
```

But payload size changes:

```text
1ch L16: 48 samples * 2 bytes * 1 channel = 96 bytes
2ch L16: 48 samples * 2 bytes * 2 channels = 192 bytes
```

This is one of the most important ideas for scaling toward 128 channels:

```text
more channels = bigger payload
same packet time = same timestamp delta
```

Run a 2-channel test:

Terminal 1:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./inspect_rtp_packets.py --group 127.0.0.1 --count 10
```

Terminal 2:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/sender
./send_rtp_audio.sh 127.0.0.1 5004 1000000 2
```

Expected:

```text
delta_seq = 1
delta_ts = 48
payload_bytes = 192
```

