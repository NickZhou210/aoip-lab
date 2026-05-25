# Phase 24: PTP BMCA Grandmaster Selection

BMCA means Best Master Clock Algorithm.

This phase answers:

```text
Why did this machine become Grandmaster?
What would make another device win instead?
```

## Current Result

From the previous `pmc` query:

```text
portState              MASTER
grandmasterPriority1   128
gm.ClockClass          248
gm.ClockAccuracy       0xfe
gm.OffsetScaledLogVariance 0xffff
grandmasterPriority2   128
grandmasterIdentity    001c42.fffe.ee3f40
```

The current VM became Grandmaster because no better external PTP clock was
visible.

## BMCA Comparison Order

For the default IEEE 1588 style BMCA, a practical simplified comparison order
is:

```text
priority1
clockClass
clockAccuracy
offsetScaledLogVariance
priority2
clockIdentity
```

Lower value wins at the first field that differs.

References:

```text
https://docs.oracle.com/en/operating-systems/oracle-linux/8/network/network-AboutPTP.html
https://www.linuxptp.org/documentation/default/
```

## Field Meaning

### `priority1`

Manual operator preference.

Lower value is preferred.

Use case:

```text
make this device preferred as Grandmaster
```

### `clockClass`

Clock quality or traceability class.

Lower class is usually better.

Your VM reported:

```text
clockClass = 248
```

Meaning:

```text
software/local clock quality
not a professional traceable Grandmaster clock
```

### `clockAccuracy`

Clock accuracy category.

Your VM reported:

```text
clockAccuracy = 0xfe
```

Meaning:

```text
accuracy unknown
```

### `offsetScaledLogVariance`

Clock stability metric.

Your VM reported:

```text
offsetScaledLogVariance = 0xffff
```

Meaning:

```text
worst/unknown stability in this simplified learning context
```

### `priority2`

Second manual preference.

This is commonly used as a tie breaker after clock quality fields.

### `clockIdentity`

Final deterministic tie breaker.

If all earlier fields tie, the lower clock identity wins.

## Run The BMCA Model

```bash
cd ~/aoip-lab/project3_ptp/scripts
./compare_ptp_clocks.py
```

Expected shape:

```text
rank name                       priority1 clockClass clockAccuracy offsetScaledLogVariance priority2 clockIdentity
0001 better-grandmaster               100        248 0xfe          0xffff                        128 001c42fffeaaaaaa
0002 same-priority-better-class       128        127 0xfe          0xffff                        128 001c42fffebbbbbb
0003 current-vm                       128        248 0xfe          0xffff                        128 001c42fffeee3f40
```

In that default example, `better-grandmaster` wins because `priority1=100` beats
`priority1=128`.

Important detail:

```text
priority1 is checked before clockClass
```

So a manually preferred clock can win even if another clock has a better class.

## Custom Candidate Example

```bash
./compare_ptp_clocks.py \
  --candidate name=vm,priority1=128,clockClass=248,clockAccuracy=0xfe,offsetScaledLogVariance=0xffff,priority2=128,clockIdentity=001c42.fffe.ee3f40 \
  --candidate name=device,priority1=127,clockClass=248,clockAccuracy=0xfe,offsetScaledLogVariance=0xffff,priority2=128,clockIdentity=001c42.fffe.aaaaaa
```

Expected result:

```text
selected_grandmaster: device
```

Because:

```text
priority1 127 beats priority1 128
```

## Why This Matters For AES67

AES67 devices need to agree on a PTP Grandmaster.

If two devices both think they should be master, the system can become unstable
or split into multiple timing islands.

The practical engineering rule is:

```text
choose the intended Grandmaster explicitly
set priorities so the intended backup order is deterministic
verify the result with pmc or Wireshark
```

For the current VM-only lab:

```text
there is only one visible PTP clock
so the VM becomes MASTER
```

A real slave/offset test requires at least one more PTP-capable node.
