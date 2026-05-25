#!/usr/bin/env bash
set -euo pipefail

COMMANDS=(
  "GET PORT_DATA_SET"
  "GET CURRENT_DATA_SET"
  "GET PARENT_DATA_SET"
  "GET TIME_STATUS_NP"
)

echo "Querying running ptp4l status with pmc"
echo
echo "Keep ptp4l running in another terminal before using this script."
echo

for command in "${COMMANDS[@]}"; do
  echo "== ${command} =="
  pmc -u -b 0 "${command}" || true
  echo
done
