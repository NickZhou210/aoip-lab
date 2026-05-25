# Phase 10: Config-Driven Sender

The sender can now read `streams.json`.

Instead of manually typing:

```bash
./send_rtp_audio.sh 127.0.0.1 5004 1000000 8
```

run:

```bash
cd ~/aoip-lab/project2_rtp_audio_stream/scripts
./send_stream_from_config.py --stream 1 --host 127.0.0.1
```

Meaning:

```text
--stream 1
```

selects this object from `config/streams.json`:

```text
stream-01
channels 1-8
group 239.69.1.1
port 5004
payload 768 bytes
```

For local learning, `--host 127.0.0.1` overrides the multicast group and sends
to loopback. This avoids VM multicast behavior while keeping the same channel
count, port, packet time, and payload size.

Expected inspector result:

```text
delta_seq = 1
delta_ts = 48
payload_bytes = 768
```

Why this matters:

```text
manual command -> config-driven system
single 8ch stream -> repeatable 128ch architecture
```

