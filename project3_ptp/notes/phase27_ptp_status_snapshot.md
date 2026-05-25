# Phase 27: PTP Status Snapshot

This phase adds one command for checking PTP state.

## Why This Exists

Before multicast or real device interoperability, we need a repeatable way to
answer:

```text
is ptp4l running?
what domain are we querying?
is the port MASTER or SLAVE?
who is the Grandmaster?
what is offsetFromMaster?
what is meanPathDelay?
```

Manual `pmc` commands work, but they are easy to mistype.

## Run Command

Start `ptp4l` in one terminal:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./run_ptp4l_software.sh enp0s5
```

In another terminal:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./ptp_status_snapshot.py --domain 0
```

If `ptp4l` is not running, the script exits early with:

```text
ptp4l is not running. Start ptp4l first, then run this snapshot command again.
```

If you are testing domain 1:

```bash
./ptp_status_snapshot.py --domain 1
```

## What It Queries

The script runs `pmc` for:

```text
GET PORT_DATA_SET
GET CURRENT_DATA_SET
GET PARENT_DATA_SET
GET TIME_STATUS_NP
```

It then extracts the key fields into one summary.

## Important Fields

```text
portState
```

Expected values:

```text
MASTER
SLAVE
LISTENING
FAULTY
```

```text
grandmasterIdentity
```

The clock identity of the current Grandmaster.

```text
offsetFromMaster
```

Meaningful when this node is following another master.

```text
meanPathDelay
```

Estimated path delay to the master.

## Current VM Expectation

With only this VM visible:

```text
portState MASTER
stepsRemoved 0
offsetFromMaster 0.0
meanPathDelay 0.0
grandmasterIdentity 001c42.fffe.ee3f40
```

That confirms the VM is acting as the software Grandmaster.

It still does not prove slave synchronization.
