#!/bin/bash
# Compile a unit blob on the droplet's QEMU instead of locally.
# Usage: droplet_compile.sh <blob> <out.cdx>
#
# Synchronous by design: the ssh holds until the guest exits, streams
# ring_compile's log lines (READY, stream:, SIZE:) into this terminal
# live, and propagates the exit code -- completion needs no polling and
# failure needs no forensics. flock -n refuses a second job loudly (the
# per-host one-compute-job rule); nice keeps the live site responsive.
#
# CODEX_MEM_MB=1300: the droplet has 2 GB total, no swap, and shares the
# box with the site. If a compile OOMs the guest at 1300, that is a real
# sizing fact to record, not a number to bump quietly.
#
# TCG on purpose, measured 2026-08-20 (JUSTIFICATIONS.md): this guest
# streams its output through port I/O, and under KVM every port access is
# a vmexit -- KVM ran the warmup blob in 43s to TCG's 26s on this box.
set -e
HOST=steve@162.243.1.123
BLOB=$1
OUT=$2
[ -s "$BLOB" ] || { echo "no blob at $BLOB"; exit 1; }

scp -q "$BLOB" "$HOST:ring/job.blob"
ssh "$HOST" 'cd ring && rm -f out.cdx out.cdx.map out.cdx.diags job.blob.stage1 && CODEX_ACCEL=tcg CODEX_MEM_MB=1300 nice -n 15 flock -n lock python3 -u ring_compile.py job.blob out.cdx'
rm -f "$OUT" "$OUT.map" "$OUT.diags"
scp -q "$HOST:ring/out.cdx" "$OUT"
scp -q "$HOST:ring/out.cdx.map" "$OUT.map" 2>/dev/null || true
scp -q "$HOST:ring/out.cdx.diags" "$OUT.diags" 2>/dev/null || true
[ -s "$OUT" ] || { echo "no CDX came back"; exit 1; }
