# Phase 25: PTP Config Experiments

This phase turns BMCA concepts into concrete `ptp4l` configuration files.

## Config Files

Current learning configs:

```text
aes67-software-ptp.cfg
aes67-preferred-master.cfg
aes67-backup-master.cfg
aes67-domain-1.cfg
aes67-client-only.cfg
```

All configs use:

```text
time_stamping = software
network_transport = UDPv4
delay_mechanism = E2E
free_running = 1
```

`free_running=1` keeps this phase observational. It avoids intentionally
disciplining the system clock while NTP/systemd-timesyncd is still active.

## Summarize Configs

Run:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./summarize_ptp_configs.py
```

This prints the key fields from each `.cfg`.

## Config Intent

### `aes67-software-ptp.cfg`

Baseline learning config.

```text
domainNumber = 0
priority1 = 128
priority2 = 128
```

This is the config used so far.

### `aes67-preferred-master.cfg`

Preferred master config.

```text
priority1 = 100
```

Because lower `priority1` wins, this clock is preferred over a default
`priority1=128` clock in the same domain.

### `aes67-backup-master.cfg`

Backup master config.

```text
priority1 = 200
```

This clock is less preferred than the baseline clock.

It can still become master if no better clock is visible.

### `aes67-domain-1.cfg`

Different PTP domain.

```text
domainNumber = 1
```

PTP domain is a timing island.

Devices in domain 0 and domain 1 do not participate in the same BMCA election.

### `aes67-client-only.cfg`

Client-only config.

```text
clientOnly = 1
```

This node should not become Grandmaster. It waits for a master.

With only one VM and no visible external master, client-only mode cannot
demonstrate a useful lock. It needs another PTP master on the network.

## What Can Be Verified With One VM

With the current single VM, we can verify:

```text
config files parse
domain and priority values are visible in config summary
clientOnly is accepted by ptp4l
```

Verified so far:

```text
summarize_ptp_configs.py reads all five config files
domainNumber / priority1 / priority2 / clientOnly / free_running are visible
```

Automatic `ptp4l` start was not run by Codex because `sudo` requires the Ubuntu
password.

Manual config start test:

```bash
cd ~/aoip-lab/project3_ptp
sudo timeout 8s ptp4l -i enp0s5 -f configs/aes67-preferred-master.cfg -m
sudo timeout 8s ptp4l -i enp0s5 -f configs/aes67-backup-master.cfg -m
sudo timeout 8s ptp4l -i enp0s5 -f configs/aes67-domain-1.cfg -m
sudo timeout 8s ptp4l -i enp0s5 -f configs/aes67-client-only.cfg -m
```

Expected one-VM behavior:

```text
preferred-master: should eventually become MASTER
backup-master: should eventually become MASTER if no better clock is visible
domain-1: should also become MASTER, but in domain 1
client-only: should stay LISTENING/UNCALIBRATED or not become MASTER without an external master
```

We cannot fully verify:

```text
actual BMCA competition between two devices
slave offset convergence
meanPathDelay to another master
failover from preferred master to backup master
```

Those require at least two PTP nodes.

## Practical AES67 Rule

For a real AES67 network:

```text
choose one intended Grandmaster
set its priority lower than other devices
put all participating devices in the same PTP domain
verify the result with pmc or Wireshark
```
