#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-enp0s5}"

echo "PTP environment check"
echo "Interface: ${IFACE}"
echo

echo "== System =="
uname -a
echo

echo "== Network =="
ip -br addr
echo
ip route show default || true
echo

echo "== PTP tools =="
for tool in ptp4l phc2sys pmc ethtool timedatectl; do
  if command -v "${tool}" >/dev/null 2>&1; then
    printf "%-12s %s\n" "${tool}" "$(command -v "${tool}")"
  else
    printf "%-12s %s\n" "${tool}" "missing"
  fi
done
echo

echo "== Interface timestamping =="
if command -v ethtool >/dev/null 2>&1; then
  ethtool -T "${IFACE}" || true
else
  echo "ethtool is missing"
fi
echo

echo "== PTP hardware clocks =="
if ls /dev/ptp* >/dev/null 2>&1; then
  ls -l /dev/ptp*
else
  echo "No /dev/ptp* devices found"
fi
echo

echo "== System time sync =="
timedatectl status || true
echo

echo "== Time services =="
for service in systemd-timesyncd chrony ntpsec ntp; do
  state="$(systemctl is-active "${service}" 2>/dev/null || true)"
  if [ -n "${state}" ]; then
    printf "%-20s %s\n" "${service}" "${state}"
  fi
done

