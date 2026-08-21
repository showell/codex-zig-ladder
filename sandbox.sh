#!/bin/bash
# One directory per experiment, so no two runs can reach the same file.
#
# The failure this exists to prevent is not "a run crashed" -- it is a run
# that READS yesterday's artifact and passes. Every ladder output
# (ast/*.truth, *.prov, *.ir, *.zig, native/*) is gitignored, so a shared
# checkout accumulates a full set of plausible, real, stale files under
# exactly the names the next run looks for. Instrumented binaries are worse
# again: 2026-08-21 left a debug-instrumented native/codexir and a
# clobbered ast/codexir.zig in the shared tree, either of which would have
# been used silently.
#
# A sandbox is two detached git worktrees plus an env file. Worktrees share
# the object store, so the cost is the working tree and not the history, and
# a fresh one carries NO gitignored artifacts at all -- which is the point.
# A run that needs natives must build them or be handed them on purpose.
#
#   ./sandbox.sh <label> [ladder-ref] [codex-repo] [codex-ref]
#   ./sandbox.sh --prune [keep]        keep the newest N (default 10)
#   ./sandbox.sh --list
#
# Then:  cd <path>/ladder && . ../env && ...
set -u
ROOT="${SANDBOX_ROOT:-$HOME/runs}"
LADDER_SRC="${LADDER_SRC:-$HOME/showell_repos/codex-zig-ladder}"

die() { echo "sandbox: $*" >&2; exit 1; }

case "${1:-}" in
    --list)
        ls -1dt "$ROOT"/*/ 2>/dev/null || echo "(no sandboxes)"
        exit 0 ;;
    --prune)
        keep="${2:-10}"
        mapfile -t old < <(ls -1dt "$ROOT"/*/ 2>/dev/null | tail -n +$((keep + 1)))
        [ ${#old[@]} -eq 0 ] && { echo "sandbox: nothing to prune (keeping $keep)"; exit 0; }
        for d in "${old[@]}"; do
            echo "pruning $d"
            for w in "$d"ladder "$d"codex; do
                [ -d "$w" ] && git -C "$w" rev-parse --git-dir >/dev/null 2>&1 \
                    && git -C "$(git -C "$w" rev-parse --path-format=absolute --git-common-dir)/.." worktree remove --force "$w" 2>/dev/null
            done
            rm -rf "$d"
        done
        git -C "$LADDER_SRC" worktree prune
        exit 0 ;;
    "" ) die "usage: sandbox.sh <label> [ladder-ref] [codex-repo] [codex-ref]" ;;
esac

label="$1"
[[ "$label" =~ ^[A-Za-z0-9._-]+$ ]] || die "label must be [A-Za-z0-9._-]"
ladder_ref="${2:-HEAD}"
codex_src="${3:-$HOME/showell_repos/NewRepository}"
codex_ref="${4:-HEAD}"

[ -d "$LADDER_SRC/.git" ] || die "no ladder repo at $LADDER_SRC"
[ -d "$codex_src/.git" ] || [ -f "$codex_src/.git" ] || die "no codex repo at $codex_src"

run="$ROOT/$(date -u +%Y%m%dT%H%M%SZ)-$label"
mkdir -p "$run" || die "cannot create $run"

git -C "$LADDER_SRC" worktree add --no-progress --detach "$run/ladder" "$ladder_ref" >/dev/null 2>&1 \
    || die "ladder worktree failed at $ladder_ref"
git -C "$codex_src" worktree add --no-progress --detach "$run/codex" "$codex_ref" >/dev/null 2>&1 \
    || { git -C "$LADDER_SRC" worktree remove --force "$run/ladder"; die "codex worktree failed at $codex_ref"; }

# Sourced by every command in the sandbox. CODEX_ROOT points INSIDE the
# sandbox on purpose: a pull in the shared checkout mid-run is then not a
# thing that can happen.
cat > "$run/env" <<EOF
export CODEX_ROOT="$run/codex"
export SANDBOX="$run"
# Host tuning belongs to the host, not to the experiment. The droplet caps
# guests at 1300 MB and pins TCG; the laptop wants the tool defaults, and a
# native build inside a 1300 MB guest does not finish. Baking one venue's
# numbers into a host-agnostic script is how that failure arrives silently.
[ -f "\$HOME/.codex_ladder_env" ] && . "\$HOME/.codex_ladder_env"
EOF

{
    echo "label       $label"
    echo "created     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "host        $(hostname)"
    echo "ladder      $(git -C "$run/ladder" rev-parse HEAD)  ($ladder_ref)"
    echo "ladder-desc $(git -C "$run/ladder" log --oneline -1)"
    echo "codex-src   $codex_src"
    echo "codex       $(git -C "$run/codex" rev-parse HEAD)  ($codex_ref)"
    echo "codex-desc  $(git -C "$run/codex" log --oneline -1 | cut -c1-90)"
} > "$run/MANIFEST"

echo "$run"
echo "--- MANIFEST"
sed 's/^/    /' "$run/MANIFEST"
echo "--- use it"
echo "    cd $run/ladder && . ../env"
echo "    (no natives, no truths, no artifacts -- a fresh tree carries none)"
