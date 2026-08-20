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
T="$(cd "$(dirname "$0")" && pwd)"
REPO="$(python3 "$T/ladder_root.py" codex)"
HOST=steve@162.243.1.123
# Keepalives, because the held ssh IS the job: a dropped link (wifi blip,
# 2026-08-20, mid-sweep) SIGHUPs the remote session, which takes the
# guest with it -- and without these the laptop side hangs on the dead
# connection for hours, indistinguishable from a long compile. With them
# it fails in about a minute, loudly, at the wrapper that can say so.
SSH_OPTS="-o ServerAliveInterval=15 -o ServerAliveCountMax=4 -o ConnectTimeout=20"
BLOB=$1
OUT=$2
[ -s "$BLOB" ] || { echo "no blob at $BLOB"; exit 1; }

# The seed check runs per-job, not per-push: the appliance's copy must be
# byte-identical to the checkout's or the compile refuses before QEMU
# boots -- the same discipline plug_run_ring applies to a stale ringplug.
# A droplet compile against last Update's seed would bank truth nobody
# named; droplet_vm_setup.sh is the fix the refusal names.
SEED_SHA=$(sha256sum "$REPO/seed/Codex.cdx" | cut -d' ' -f1)

scp -q $SSH_OPTS "$BLOB" "$HOST:ring/job.blob"
ssh $SSH_OPTS "$HOST" "cd ring && [ \"\$(sha256sum seed/Codex.cdx | cut -d' ' -f1)\" = \"$SEED_SHA\" ] || { echo 'SEED STALE on droplet vs the checkout -- run droplet_vm_setup.sh'; exit 1; } && rm -f out.cdx out.cdx.map out.cdx.diags job.blob.stage1 && CODEX_ACCEL=tcg CODEX_MEM_MB=1300 nice -n 15 flock -n lock python3 -u ring_compile.py job.blob out.cdx"
rm -f "$OUT" "$OUT.map" "$OUT.diags"
scp -q $SSH_OPTS "$HOST:ring/out.cdx" "$OUT"
scp -q $SSH_OPTS "$HOST:ring/out.cdx.map" "$OUT.map" 2>/dev/null || true
scp -q $SSH_OPTS "$HOST:ring/out.cdx.diags" "$OUT.diags" 2>/dev/null || true
[ -s "$OUT" ] || { echo "no CDX came back"; exit 1; }
