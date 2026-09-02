#!/bin/bash
# One directory per experiment, and a written record of what built it.
#
# A sandbox does exactly two things.
#
# ISOLATION. The failure this exists to prevent is not "a run crashed" -- it is
# a run that READS yesterday's artifact and passes. Every ladder output
# (ast/*.truth, *.prov, *.ir, *.zig, native/*) is gitignored, so a shared
# checkout accumulates a full set of plausible, real, stale files under exactly
# the names the next run looks for. Instrumented binaries are worse again:
# 2026-08-21 left a debug-instrumented native/codexir and a clobbered
# ast/codexir.zig in the shared tree, either of which would have been used
# silently. A sandbox is two detached git worktrees plus an env file; worktrees
# share the object store, so the cost is the working tree and not the history,
# and a fresh one carries NO gitignored artifacts at all. A run that needs
# natives must build them or be handed them on purpose.
#
# PROVENANCE. A result is only worth as much as the record of what produced it,
# and that record has to be COMPLETE rather than convenient. The components are
# enumerated in write_provenance below -- one row each, nothing decides a result
# without a row -- and adding a component is adding a line there.
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

# THE SOURCE MUST BE COMMITTED, and this refuses rather than recording a flag.
# A sha is the whole of a sandbox's provenance and a sha taken over a dirty tree
# is a false statement about what ran -- the sandbox would say `1481180` and
# hold something no commit contains. Steve's rule and it is the right one:
# there is no reason to start a sandbox from uncommitted code, and commits cost
# nothing. So an experiment is a COMMIT, and the sandbox is cut from it; the
# record then points at something anyone can check out.
require_clean() {           # <repo> <what>
    local dirty
    dirty=$(git -C "$1" status --porcelain 2>/dev/null) || die "not a git repo: $1"
    [ -z "$dirty" ] && return 0
    {
        echo "sandbox: $2 has uncommitted changes and a sandbox is cut from a sha:"
        printf '%s\n' "$dirty" | head -10 | sed 's/^/    /'
        [ "$(printf '%s\n' "$dirty" | wc -l)" -gt 10 ] && echo "    ... and more"
        echo "  commit them (they cost nothing) and cut the sandbox from the commit."
    } >&2
    exit 1
}

# WHICH BRANCH, which is the question a sha does not answer. The worktree is
# detached by design, so this asks the SOURCE repo at cut time: the branch the
# requested ref names, or the branch the source was on when the ref was HEAD.
# `none` is honest for a tag, a remote ref or a bare sha -- the `-ref` row
# beside it still records what was asked for.
branch_of() {               # <repo> <ref>
    local b
    if [ "$2" = HEAD ]; then
        b=$(git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null)
        [ -n "$b" ] && [ "$b" != HEAD ] && { echo "$b"; return; }
    elif git -C "$1" show-ref --verify --quiet "refs/heads/$2"; then
        echo "$2"; return
    fi
    echo none
}

prov()     { printf '%s\t%s\n' "$1" "$2"; }
prov_get() { awk -F'\t' -v k="$2" '$1 == k { print $2; exit }' "$1" 2>/dev/null; }

case "${1:-}" in
    --list)
        listed=0
        for d in $(ls -1dt "$ROOT"/*/ 2>/dev/null); do
            listed=1
            echo "$d"
            # A sandbox cut before PROVENANCE existed is NAMED as such rather
            # than parsed. Carrying a reader for a retired format is how the
            # old MANIFEST ended up with two spellings of every key.
            #
            # PROVENANCE is deliberately the same word a gold bank and the
            # transpiler repos use -- it means the same thing -- so the row
            # that identifies OURS is checked rather than the filename.
            # ~/runs/stale-zig-plug-2026-08-26-a961dcb6 is a bank, not a
            # sandbox, and read as one it reported two missing worktrees as
            # though something had gone wrong.
            if [ ! -f "${d}PROVENANCE" ] || [ -z "$(prov_get "${d}PROVENANCE" ladder-sha)" ]; then
                if [ -f "${d}MANIFEST" ]; then
                    echo "    (MANIFEST-era sandbox -- provenance not comparable)"
                elif [ -f "${d}PROVENANCE" ]; then
                    echo "    (not a sandbox -- PROVENANCE, but no ladder-sha)"
                else
                    echo "    (no provenance)"
                fi
                continue
            fi
            for w in ladder codex; do
                rec=$(prov_get "${d}PROVENANCE" "$w-sha")
                br=$(prov_get "${d}PROVENANCE" "$w-branch")
                live=$(git -C "${d}${w}" rev-parse HEAD 2>/dev/null)
                if [ -z "$live" ]; then
                    printf '    %-7s (no worktree)\n' "$w"
                elif [ "$live" = "$rec" ]; then
                    printf '    %-7s %s  %s\n' "$w" "${live:0:8}" "$br"
                else
                    # The divergence is ALLOWED and being silent about it is
                    # not: a detached worktree gets moved so a branch ref can
                    # advance, which is what 20260824T132742Z-f37-parser did,
                    # and a measurement was nearly attributed to the wrong tree
                    # on the strength of a record that had not noticed.
                    printf '    %-7s %s  MOVED -- cut from %s (%s)\n' \
                        "$w" "${live:0:8}" "${rec:0:8}" "$br"
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

# Asked BEFORE anything is created, so a refusal leaves no half-built run.
require_clean "$LADDER_SRC" "the ladder ($LADDER_SRC)"
require_clean "$codex_src" "the codex checkout ($codex_src)"

ladder_branch=$(branch_of "$LADDER_SRC" "$ladder_ref")
codex_branch=$(branch_of "$codex_src" "$codex_ref")

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

# THE HOST'S TUNING IS FROZEN INTO THE SANDBOX, not re-read on every use.
#
# It used to be a `. ~/.codex_ladder_env` in the env file, which meant guest
# size and accel were decided at USE time and no run recorded which it got.
# That is not academic: `run_cdx` handed every run-stage guest 1024 MB while
# the droplet exported 3072, changing guest size moves every truth, and no
# sandbox on disk says which of the two it ran under.
#
# Freezing does not fight the rule the old comment was defending. That rule is
# that a host-agnostic SCRIPT must not carry one venue's numbers -- the 2 GB
# site box needed 1300 where the droplet wants 3072 -- and it is untouched:
# the values are still the host's, read from the host's file. What changes is
# that an INSTANCE pins them, so it runs tomorrow the way it ran today and its
# provenance is true. A host retune reaches the next sandbox, not this one.
#
# Only variables the host actually set are exported: `compare_arms.py` refuses
# a sandbox whose env yields no CODEX_LADDER_VENUE, and that refusal has to
# keep working on a host that sets none.
frozen=$(
    if [ -f "$HOME/.codex_ladder_env" ]; then . "$HOME/.codex_ladder_env"; fi
    for v in CODEX_LADDER_VENUE CODEX_MEM_MB CODEX_ACCEL; do
        eval "val=\${$v-}"
        [ -n "$val" ] && printf 'export %s=%s\n' "$v" "$val"
    done
    :
)

# No backticks in here: the heredoc is unquoted so they would run. The trailing
# colon keeps the file's exit status 0 -- a source that returns non-zero
# silently short-circuits the caller's and-chain, which cost one build launch.
cat > "$run/env" <<EOF
export CODEX_ROOT="$run/codex"
export SANDBOX="$run"
$frozen
:
EOF

frozen_value() { printf '%s\n' "$frozen" | sed -n "s/^export $1=//p"; }

# THE COMPONENT LIST. Everything that decides a result gets a row, and nothing
# decides a result without one -- so adding a component is adding a line here
# rather than remembering to write it somewhere.
#
# The seed is the row banked truth is meaningless without: `seed/Codex.cdx` is
# what compiles every subject, and the Update number people say out loud is
# DERIVED from its hash rather than typed beside it. It is knowable at cut time
# because the codex sha pins it.
write_provenance() {
    prov label         "$label"
    prov created       "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    prov host          "$(hostname)"
    prov venue         "$(frozen_value CODEX_LADDER_VENUE)"
    prov guest-mem-mb  "$(frozen_value CODEX_MEM_MB)"
    prov accel         "$(frozen_value CODEX_ACCEL)"
    prov ladder-repo   "$LADDER_SRC"
    prov ladder-branch "$ladder_branch"
    prov ladder-ref    "$ladder_ref"
    prov ladder-sha    "$(git -C "$run/ladder" rev-parse HEAD)"
    prov ladder-subject "$(git -C "$run/ladder" log --oneline -1 | cut -c1-90)"
    prov codex-repo    "$codex_src"
    prov codex-branch  "$codex_branch"
    prov codex-ref     "$codex_ref"
    prov codex-sha     "$(git -C "$run/codex" rev-parse HEAD)"
    prov codex-subject "$(git -C "$run/codex" log --oneline -1 | cut -c1-90)"
    prov seed-sha256   "$seed_sha"
    prov seed-update   "$seed_update"
}

# Derived from the worktree that was just cut, so it describes THIS sandbox's
# checkout and not the shared one. A seed no release note names is not an
# error -- it is an unreleased or locally rebuilt seed, and it says so.
seed_read=$(CODEX_ROOT="$run/codex" python3 -c '
import sys
sys.path.insert(0, sys.argv[1])
import seed_identity
sha = seed_identity.seed_sha256()
print(sha)
print(seed_identity.update_label(sha) or "unreleased")
' "$run/ladder" 2>/dev/null) || die "cannot read the seed in $run/codex"
seed_sha=$(printf '%s\n' "$seed_read" | sed -n 1p)
seed_update=$(printf '%s\n' "$seed_read" | sed -n 2p)

write_provenance > "$run/PROVENANCE"

# The path is the only thing on stdout, so `S=$(./sandbox.sh label)` is exact.
# Everything a human wants goes to stderr.
{
    echo "--- PROVENANCE"
    sed 's/^/    /' "$run/PROVENANCE" | expand -t 4,22
    echo "--- use it"
    echo "    cd $run/ladder && . ../env"
    echo "    (no natives, no truths, no artifacts -- a fresh tree carries none)"
} >&2
echo "$run"
