# Phase 2: Multicast Troubleshooting

Multicast is a network behavior, not an RTP behavior.

The current VM has:

```text
interface: enp0s5
ip: 10.211.55.6
multicast test group: 239.69.1.1
port: 5004
```

Important lesson from testing:

- RTP packet generation works.
- Unicast RTP to `127.0.0.1:5004` works.
- Clean local multicast receive needs more VM/network investigation.

This is normal for AoIP work. Multicast depends on:

- sender interface
- receiver interface
- multicast group membership
- VM network mode
- switch/IGMP behavior on real networks
- whether multicast loopback is enabled for same-machine tests

Current sender uses:

```text
multicast-iface=enp0s5
loop=true
ttl-mc=16
```

Do not treat multicast as "just a different IP address." It is a separate
network-layer topic.

