# Phase 15: PTP First Checks

PTP means Precision Time Protocol.

For AES67, RTP moves the audio packets, but PTP gives devices a shared clock.

Simple mental model:

```text
RTP = carries audio
SDP = describes audio
PTP = aligns clocks
```

## Current VM Finding

The current Ubuntu VM interface is:

```text
enp0s5
10.211.55.6
```

Its timestamping capability is software-only:

```text
software-transmit
software-receive
software-system-clock
PTP Hardware Clock: none
```

This means:

```text
good for learning ptp4l logs and concepts
not representative of hardware-accurate AES67 timing
```

Real AES67 systems normally benefit from hardware timestamping and a PTP
Hardware Clock, often visible as:

```text
/dev/ptp0
```

## Install linuxptp

The tools we need are in the `linuxptp` package:

```bash
sudo apt-get update
sudo apt-get install -y linuxptp
```

After installation, these commands should exist:

```text
ptp4l
phc2sys
pmc
```

## Check Environment

Run:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./check_ptp_environment.sh enp0s5
```

This checks:

- whether linuxptp tools are installed.
- whether the NIC has hardware timestamping.
- whether `/dev/ptp*` exists.
- whether NTP/systemd-timesyncd is active.

## What The Tools Do

### `ptp4l`

Runs the PTP protocol on a network interface.

It talks to other PTP clocks and decides whether this machine is master or
slave.

### `phc2sys`

Synchronizes clocks inside the local machine.

Common jobs:

```text
PHC -> system clock
system clock -> PHC
```

PHC means PTP Hardware Clock.

### `pmc`

Management client for asking a running `ptp4l` what it is doing.

Example later:

```bash
pmc -u -b 0 'GET CURRENT_DATA_SET'
```

## Important Warning

Your current system has NTP active:

```text
systemd-timesyncd = active
```

Do not let NTP and PTP both discipline the same system clock during a real test.
For first learning, we will inspect and run `ptp4l` carefully before changing
system clock behavior.

