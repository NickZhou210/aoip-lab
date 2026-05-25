# Phase 9: Stream Config

The stream plan now exists as JSON:

```text
project2_rtp_audio_stream/config/streams.json
```

This file is the first machine-readable 128-channel architecture.

It says:

```text
128 total channels
16 RTP streams
8 channels per stream
L16
48 kHz
1 ms packet time
payload type 96
```

Each stream has:

- name
- multicast group
- UDP port
- channel start/end
- payload size
- MTU check

Why this matters:

```text
humans should not manually remember 16 stream addresses
scripts should read one config file
SDP generation should come from the same config
sender startup should come from the same config
```

Regenerate it with:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./plan_streams.py --total-channels 128 --channels-per-stream 8 --json-out ../config/streams.json
```

