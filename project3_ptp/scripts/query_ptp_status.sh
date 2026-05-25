#!/usr/bin/env bash
set -euo pipefail

COMMANDS=(
  "GET PORT_DATA_SET"
  "GET CURRENT_DATA_SET"
  "GET PARENT_DATA_SET"
  "GET TIME_STATUS_NP"
)

if [ "$(id -u)" -eq 0 ]; then
  PMC=(pmc)
else
  PMC=(sudo pmc)
fi

echo "Querying running ptp4l status with pmc"
echo
echo "Keep ptp4l running in another terminal before using this script."
echo "This script uses sudo for pmc when needed because ptp4l was started as root."
echo

for command in "${COMMANDS[@]}"; do
  echo "== ${command} =="
  "${PMC[@]}" -u -b 0 "${command}" || true
  echo
done
