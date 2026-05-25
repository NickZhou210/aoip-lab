# Phase 14: All Streams Test

The project can now test every configured RTP stream:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_all_streams.py
```

It runs:

```text
stream-01
stream-02
...
stream-16
```

Each stream should create an 8-channel, 48 kHz WAV file.

This proves the local 128-channel split plan is internally consistent:

```text
16 streams * 8 channels = 128 channels
```

This is still local loopback testing, not full AES67 network interoperability.
But it is a serious engineering checkpoint.

