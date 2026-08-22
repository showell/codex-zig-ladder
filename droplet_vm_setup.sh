#!/bin/bash
# One-time provisioning of the droplet as a remote QEMU compile appliance
# (design: claude-steve/random893.md, agreed Steve + Claude 2026-08-20).
#
# The droplet holds NO logic and no checkout -- only qemu, the two driver
# scripts it is handed verbatim, a two-line ladder_root stub, and the seed
# kernel. Re-run this script whenever the seed re-pins or the drivers
# change; it is idempotent and re-pushes everything.
#
# The live site shares the box: nothing here installs a service, opens a
# port, or touches the site's files. Day-to-day jobs run via
# droplet_compile.sh, niced and flocked.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
REPO="$(python3 "$T/ladder_root.py" codex)"
HOST=steve@143.244.172.148

ssh "$HOST" 'sudo -n apt-get -qq install -y qemu-system-x86 >/dev/null && sudo -n usermod -aG kvm steve && mkdir -p ~/ring/seed'

scp -q "$T/ring_compile.py" "$T/codex_vm.py" "$HOST:ring/"
scp -q "$REPO/seed/Codex.cdx" "$HOST:ring/seed/Codex.cdx"

# codex_vm imports ladder_root for the checkout root; the appliance's root
# is ~/ring and the seed sits at its usual relative spot beneath it.
ssh "$HOST" 'cat > ring/ladder_root.py' <<'PY'
# Droplet appliance stub: no Codex checkout here, only kernels under ~/ring.
import pathlib
CODEX = pathlib.Path.home() / "ring"
PY

# Verify the push by content, not by trust: the seed hash must match.
# KVM is reported but not required -- the venue runs TCG on purpose
# (JUSTIFICATIONS.md, "Droplet compile venue").
LOCAL_SHA=$(sha256sum "$REPO/seed/Codex.cdx" | cut -d' ' -f1)
ssh "$HOST" "
  REMOTE_SHA=\$(sha256sum ring/seed/Codex.cdx | cut -d' ' -f1)
  [ \"\$REMOTE_SHA\" = \"$LOCAL_SHA\" ] || { echo 'SEED HASH MISMATCH'; exit 1; }
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo 'kvm: accessible (unused; TCG measured faster here)' || echo 'kvm: not accessible (fine; the venue runs TCG on purpose)'
  qemu-system-x86_64 --version | head -1
  echo 'appliance ready'
"
