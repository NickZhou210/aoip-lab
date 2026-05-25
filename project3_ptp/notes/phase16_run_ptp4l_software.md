# Phase 16: Run ptp4l In Software Observe Mode

This phase starts the first real PTP process.

The goal is not perfect AES67 timing yet. The goal is to see PTP behavior:

```text
network interface -> PTP messages -> ptp4l state machine -> master/slave logs
```

## Why This Is Observe Mode

Your VM interface currently has software timestamping only:

```text
software-transmit
software-receive
software-system-clock
PTP Hardware Clock: none
```

So the first run uses this config line:

```ini
free_running            1
```

Meaning:

```text
ptp4l may listen, talk, and print timing information
but it should not adjust the local system clock
```

This is important because your system also has NTP active:

```text
systemd-timesyncd = active
```

For learning, it is safer to observe first. Later, when we intentionally test
clock discipline, we will decide which service controls time.

## Run Command

From Ubuntu:

```bash
cd ~/aoip-lab/project3_ptp/scripts
./run_ptp4l_software.sh enp0s5
```

You will probably need your Ubuntu password because `ptp4l` needs network clock
permissions:

```text
[sudo] password for nick:
```

Stop it with:

```text
Ctrl+C
```

## What The Script Does

The script is:

```bash
#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-enp0s5}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG="${PROJECT_DIR}/configs/aes67-software-ptp.cfg"

exec sudo ptp4l -i "${IFACE}" -f "${CONFIG}" -m
```

Line by line:

- `#!/usr/bin/env bash`: run this file with Bash.
- `set -euo pipefail`: stop early if a command fails or a variable is missing.
- `IFACE="${1:-enp0s5}"`: use the first command argument as the network interface; if no argument is given, use `enp0s5`.
- `SCRIPT_DIR=...`: find the folder where this script lives.
- `PROJECT_DIR=...`: move one folder up from `scripts` to `project3_ptp`.
- `CONFIG=...`: point to the PTP config file.
- `exec sudo ptp4l ...`: replace the script process with `ptp4l`.
- `-i "${IFACE}"`: choose the network interface.
- `-f "${CONFIG}"`: load our config file.
- `-m`: print logs to the terminal.

## Important ptp4l Words

### `LISTENING`

The port is waiting for PTP announce messages.

Baby version:

```text
Are there any clocks on this network?
```

### `MASTER`

This machine believes it is the best clock currently visible.

Baby version:

```text
I cannot find a better clock, so I will be the clock leader.
```

### `SLAVE`

This machine found a better clock and is following it.

Baby version:

```text
I found a leader clock, so I will follow that clock.
```

### `FAULTY`

Something about the interface, socket, permissions, or timestamping failed.

Baby version:

```text
PTP tried to start but something is wrong.
```

## What We Expect In This VM

If there is no other PTP grandmaster on the VM network, this Ubuntu machine may
become `MASTER`.

That is not a failure. It means:

```text
PTP is running
but there is no external better clock to follow
```

For AES67 production, we eventually want a clear grandmaster clock and audio
devices following it. For this phase, we only want to understand the first logs.
