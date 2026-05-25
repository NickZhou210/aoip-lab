# Phase 13: Loopback Test Runner

The project now has a test runner for one configured stream:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./run_stream_pair.py --stream 1
```

It automatically:

1. starts the config-driven receiver.
2. starts the config-driven sender.
3. waits a few seconds.
4. stops both.
5. checks the WAV file exists.
6. checks the WAV is larger than just a header.
7. checks the WAV channel count and sample rate.

This is not an AES67 certification test. It is a local engineering sanity check.

Why this matters:

```text
manual test -> repeatable test
single stream -> all 16 streams later
```

Example:

```bash
./run_stream_pair.py --stream 1 --duration 3
```

Expected final line:

```text
PASS
```

