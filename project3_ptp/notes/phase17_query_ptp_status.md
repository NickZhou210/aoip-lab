# Phase 17: Query ptp4l With pmc

In Phase 16, `ptp4l` printed logs.

In this phase, we ask the running `ptp4l` process for structured status.

Simple mental model:

```text
ptp4l = the PTP engine
pmc   = a small tool that asks the PTP engine questions
```

## Terminal 1: Run ptp4l

```bash
cd ~/aoip-lab/project3_ptp/scripts
./run_ptp4l_software.sh enp0s5
```

Leave this running.

## Terminal 2: Query Status

Open a second terminal:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./query_ptp_status.sh
```

## What The Script Does

The script runs:

```bash
sudo pmc -u -b 0 "GET PORT_DATA_SET"
sudo pmc -u -b 0 "GET CURRENT_DATA_SET"
sudo pmc -u -b 0 "GET PARENT_DATA_SET"
sudo pmc -u -b 0 "GET TIME_STATUS_NP"
```

Line by line:

- `sudo`: use administrator permission, because `ptp4l` was started as root.
- `pmc`: PTP management client.
- `-u`: use the local Unix socket to talk to `ptp4l`.
- `-b 0`: boundary hop count 0; ask the local PTP process.
- `GET ...`: ask for one PTP data set.

## If You See Permission Denied

Error:

```text
uds: bind failed: Permission denied
failed to open transport
failed to create pmc
```

Meaning:

```text
pmc tried to talk to ptp4l through the local Unix socket
but the normal user did not have permission
```

This does not mean PTP failed.

It means:

```text
ptp4l was started with sudo
so pmc also needs sudo
```

## What To Look For

### `PORT_DATA_SET`

This tells us the state of the network port.

Important field:

```text
portState
```

Expected in this VM:

```text
portState MASTER
```

Meaning:

```text
enp0s5 is currently acting as a PTP master port
```

### `CURRENT_DATA_SET`

This is most useful when the machine is a slave following another clock.

Important fields:

```text
stepsRemoved
offsetFromMaster
meanPathDelay
```

Baby version:

```text
stepsRemoved    = how many clock hops away from the grandmaster
offsetFromMaster = how far my clock is from the master
meanPathDelay   = estimated network delay to the master
```

If this machine is the master, some offset fields may be absent or not very
interesting.

### `PARENT_DATA_SET`

This says which clock this machine treats as its parent.

If this VM is the grandmaster, the parent can effectively be itself.

### `TIME_STATUS_NP`

This is a LinuxPTP-specific time status page.

Useful fields can include:

```text
master_offset
gmIdentity
ingress_time
cumulativeScaledRateOffset
```

For the first VM-only test, the most important question is simple:

```text
Can pmc talk to ptp4l?
```

If yes, we have moved from "watching logs" to "querying PTP state."

## Observed Result On This VM

The first run without `sudo` failed:

```text
uds: bind failed: Permission denied
failed to open transport
failed to create pmc
```

After the script was updated to use `sudo pmc`, the query worked.

### `PORT_DATA_SET`

Observed:

```text
portIdentity            001c42.fffe.ee3f40-1
portState               MASTER
logMinDelayReqInterval  0
logAnnounceInterval     1
announceReceiptTimeout  3
logSyncInterval         0
delayMechanism          1
versionNumber           2
```

Meaning:

```text
the real network port is enp0s5
the port is in MASTER state
this VM is sending PTP timing as a master
PTP version is 2
```

### `CURRENT_DATA_SET`

Observed:

```text
stepsRemoved     0
offsetFromMaster 0.0
meanPathDelay    0.0
```

Meaning:

```text
stepsRemoved = 0 because this VM is the grandmaster
offsetFromMaster = 0 because a master is not following another master
meanPathDelay = 0 because there is no upstream master path to measure
```

This is expected for a single visible PTP clock.

### `PARENT_DATA_SET`

Observed:

```text
parentPortIdentity   001c42.fffe.ee3f40-0
grandmasterPriority1 128
gm.ClockClass        248
gm.ClockAccuracy     0xfe
grandmasterPriority2 128
grandmasterIdentity  001c42.fffe.ee3f40
```

Meaning:

```text
the parent and grandmaster are this same VM
priority1 and priority2 are both 128 from our config
clockClass 248 means this is not a highly accurate traceable grandmaster
```

### `TIME_STATUS_NP`

Observed:

```text
master_offset +0
cumulativeScaledRateOffset +0.000000000
gmPresent false
gmIdentity 001c42.fffe.ee3f40
```

Meaning:

```text
there is no external grandmaster present
the grandmaster identity still points to this VM
there is no measured master offset because this VM is the master
```

## Phase 17 Conclusion

We have now proved:

```text
ptp4l can run
pmc can query ptp4l
enp0s5 is in MASTER state
the VM is acting as a software grandmaster
```

We have not proved:

```text
slave synchronization
offset measurement to an external grandmaster
hardware timestamp precision
AES67-grade timing accuracy
```
