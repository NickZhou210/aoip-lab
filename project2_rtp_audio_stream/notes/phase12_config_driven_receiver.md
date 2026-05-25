# Phase 12: Config-Driven Receiver

The receiver can now read `streams.json`.

Run:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./receive_stream_from_config.py --stream 1
```

It reads:

```text
stream-01
port 5004
payload type 96
L16/48000/8
channels 1-8
```

and writes:

```text
project2_rtp_audio_stream/receiver/stream-01.wav
```

The receiver uses `gst-launch-1.0 -e` so a normal interrupt can finish the WAV
file cleanly. For manual use, stop it with `Ctrl+C`.

If the file is much larger than the 80-byte WAV header, real audio data was
written.

For short local tests, you can bypass jitter buffering:

```bash
./receive_stream_from_config.py --stream 1 --no-jitterbuffer
```

The jitter buffer is useful in real networks, but direct depay is simpler when
you only want to prove the local payload and channel format.

Test with the sender:

Terminal 1:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./receive_stream_from_config.py --stream 1
```

Terminal 2:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./send_stream_from_config.py --stream 1 --host 127.0.0.1
```

This gives the project three config-driven pieces:

```text
streams.json -> sender
streams.json -> receiver
streams.json -> SDP
```
