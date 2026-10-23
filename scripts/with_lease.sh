#!/bin/bash
# usage: with_lease.sh ITEM CMD...  (waits for codex's heavy_build lease, runs CMD, always releases)
ITEM=$1; shift
FL=~/Source/fontlab-mcp/.venv/bin/flease
until $FL acquire claude@rpi5 "$ITEM" "$*" >/dev/null 2>&1; do sleep 20; done
trap '$FL release claude@rpi5 >/dev/null 2>&1' EXIT
"$@"
