# Phase 26: PTP Domain Experiment

This phase focuses on:

```text
domainNumber
```

## Core Rule

PTP domain is a timing island.

Devices in different domains do not participate in the same BMCA election.

Practical meaning:

```text
domain 0 devices choose a domain 0 Grandmaster
domain 1 devices choose a domain 1 Grandmaster
domain 0 and domain 1 ignore each other for clock selection
```

## Current Configs

Baseline:

```text
configs/aes67-software-ptp.cfg
domainNumber 0
```

Domain 1 test:

```text
configs/aes67-domain-1.cfg
domainNumber 1
```

Both configs use:

```text
time_stamping software
network_transport UDPv4
delay_mechanism E2E
free_running 1
```

## Run Domain 1 Test

Run manually because `ptp4l` needs `sudo`:

```bash
cd ~/aoip-lab/project3_ptp
sudo timeout 8s ptp4l -i enp0s5 -f configs/aes67-domain-1.cfg -m
```

Expected one-VM behavior:

```text
INITIALIZING to LISTENING
LISTENING to MASTER
assuming the grand master role
```

Why?

```text
there is no other visible domain 1 Grandmaster
so this VM becomes master for domain 1
```

## What This Proves With One VM

With one VM, this test can prove:

```text
ptp4l accepts domainNumber 1
the domain 1 config can start
the VM can become master in domain 1 when alone
```

It cannot fully prove:

```text
domain 0 and domain 1 devices ignore each other
```

That requires two visible PTP nodes or two simultaneous PTP instances with
separate network conditions.

## Why This Matters For AES67

If an AES67 sender and receiver are in different PTP domains, they may both
appear healthy locally but still not share the same clock.

Operational rule:

```text
sender PTP domain must match receiver PTP domain
```

When comparing with Yamaha, Dante AES67 mode, Ravenna, or other devices, always
check:

```text
PTP domainNumber
Grandmaster identity
portState
offsetFromMaster
```
