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
#   ./sandbox.sh --prune [keep]        keep the newest N (default 10), and
#                                      any run holding a KEEP file, whose
#                                      first line says why
#   ./sandbox.sh --list                live head of each worktree, MOVED if it
#                                      no longer matches what it was cut from
#
# Then:  cd <path>/ladder && . ../env && ...
set -u
ROOT="${SANDBOX_ROOT:-$HOME/runs}"
LADDER_SRC="${LADDER_SRC:-$HOME/showell_repos/codex-zig-ladder}"

die() { echo "sandbox: $*" >&2; exit 1; }

# The MANIFEST records what a worktree was cut FROM. Git records what it holds
# NOW, and the two diverge legitimately: a detached worktree gets moved so a
# branch ref can advance, which is what 20260824T132742Z-f37-parser did. The
# divergence is allowed; it being SILENT is not. That MANIFEST went on reading
# `codex 8cb8a0e4` while the tree held 65cb244b, and a measurement was nearly
# attributed to the wrong tree on the strength of it. So --list answers from
# git, which is always current, and prints the recorded commit only as the
# provenance it actually is.
manifest_field() {          # <manifest> <worktree> -> recorded sha, or empty
    # Reads the current `<name>-at-creation` key and the bare `<name>` key
    # written before 2026-08-24, because the sandboxes that exposed this are
    # still on disk and are precisely the ones worth checking.
    awk -v a="$2-at-creation" -v b="$2" \
        '$1 == a { print $2; exit } $1 == b { print $2; exit }' "$1" 2>/dev/null
}

case "${1:-}" in
    --list)
        listed=0
        for d in $(ls -1dt "$ROOT"/*/ 2>/dev/null); do
            listed=1
            echo "$d"
            for w in ladder codex; do
                rec=$(manifest_field "${d}MANIFEST" "$w")
                live=$(git -C "${d}${w}" rev-parse HEAD 2>/dev/null)
                if [ -z "$live" ]; then
                    printf '    %-7s (no worktree)\n' "$w"
                elif [ -z "$rec" ]; then
                    printf '    %-7s %s  (MANIFEST does not say)\n' "$w" "${live:0:8}"
                elif [ "$live" = "$rec" ]; then
                    printf '    %-7s %s\n' "$w" "${live:0:8}"
                else
                    printf '    %-7s %s  MOVED -- cut from %s\n' \
                        "$w" "${live:0:8}" "${rec:0:8}"
                fi
            done
        done
        [ "$listed" = 1 ] || echo "(no sandboxes)"
        exit 0 ;;
    --prune)
        keep="${2:-10}"
        mapfile -t old < <(ls -1dt "$ROOT"/*/ 2>/dev/null | tail -n +$((keep + 1)))
        [ ${#old[@]} -eq 0 ] && { echo "sandbox: nothing to prune (keeping $keep)"; exit 0; }
        for d in "${old[@]}"; do
            # A run holding a KEEP file is not scratch. Newest-N is the wrong
            # rule for a run that is an ORACLE rather than a by-product: the
            # unshaken emitted corpus is the input every --check-corpus and
            # --prove-gate needs, and once the shake is on nothing regenerates
            # it. Age says nothing about that. KEEP says why, in the file.
            if [ -f "$d/KEEP" ]; then
                echo "keeping $d -- $(head -1 "$d/KEEP")"
                continue
            fi
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

# -q, not --no-progress: the latter is not an option to `worktree add` on
# every git, and swallowing stderr hid that for a whole debugging round.
# Errors are captured and reported, never discarded.
if ! err=$(git -C "$LADDER_SRC" worktree add -q --detach "$run/ladder" "$ladder_ref" 2>&1); then
    rmdir "$run" 2>/dev/null
    die "ladder worktree failed at $ladder_ref: $err"
fi
if ! err=$(git -C "$codex_src" worktree add -q --detach "$run/codex" "$codex_ref" 2>&1); then
    git -C "$LADDER_SRC" worktree remove --force "$run/ladder" 2>/dev/null
    rmdir "$run" 2>/dev/null
    die "codex worktree failed at $codex_ref: $err"
fi

# Sourced by every command in the sandbox. CODEX_ROOT points INSIDE the
# sandbox on purpose: a pull in the shared checkout mid-run is then not a
# thing that can happen.
cat > "$run/env" <<EOF
export CODEX_ROOT="$run/codex"
export SANDBOX="$run"
# Host tuning belongs to the host, not to the experiment. The droplet pins
# its guest ceiling (3072 MB) and TCG in ~/.codex_ladder_env; the laptop
# wants the tool defaults. When the 2 GB site box was the venue its 1300 MB
# cap made a native build hang rather than fail, and baking one venue's
# numbers into a host-agnostic script is how that failure arrives silently.
if [ -f "\$HOME/.codex_ladder_env" ]; then . "\$HOME/.codex_ladder_env"; fi
# Sourcing this must succeed even when the host file is absent: a trailing
# test that fails makes the source return 1 and silently short-circuits the
# caller's and-chain, which cost one build launch. Hence the trailing colon.
# No backticks in here: the heredoc is unquoted so they would run.
:
EOF

{
    echo "label       $label"
    echo "created     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "host        $(hostname)"
    echo "ladder-at-creation $(git -C "$run/ladder" rev-parse HEAD)  ($ladder_ref)"
    echo "ladder-desc $(git -C "$run/ladder" log --oneline -1)"
    echo "codex-src   $codex_src"
    echo "codex-at-creation  $(git -C "$run/codex" rev-parse HEAD)  ($codex_ref)"
    echo "codex-desc  $(git -C "$run/codex" log --oneline -1 | cut -c1-90)"
} > "$run/MANIFEST"

# The path is the only thing on stdout, so `S=$(./sandbox.sh label)` is exact.
# Everything a human wants goes to stderr.
{
    echo "--- MANIFEST"
    sed 's/^/    /' "$run/MANIFEST"
    echo "--- use it"
    echo "    cd $run/ladder && . ../env"
    echo "    (no natives, no truths, no artifacts -- a fresh tree carries none)"
} >&2
echo "$run"
