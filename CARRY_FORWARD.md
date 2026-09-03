# Carry forward: the earned-knowledge ledger

Every fix we make is destined for an Update we do not control. Between making
it and Damian taking it, the fix lives on a branch -- and the branch is the
only thing that remembers. This file says which branch, on which base, proven
how, and where the progression restarts.

**The rule this file exists to enforce: a branch that cost work is never
deleted, only superseded.** Branches are cheap. Re-derivation is not. On
2026-09-03 I deleted `u55-driver` in codex-zig-transpiler because I had decided
its approach was wrong -- but the branch was not an approach, it was a day's
earned knowledge about how `compile-frontend-cdx` is called. It was recoverable
from the reflog. The next one might not be.

## The process

1. **Learn the issue.** A reproduction, isolated, with the failing output kept.
2. **Make the fix.** On a branch, committed. Never in a scratch tree.
3. **Update the working branch.** The fix joins the accumulating superset, which
   only ever grows. It stays there until upstream takes it.
4. **Find the restart point.** The fix changes the target, so re-entry is
   wherever the fix could have invalidated a prior result -- not from the top,
   and not from where we happened to stop.

Step 4 is the one that gets skipped. A fix to the zig plug invalidates every
zig-arm result taken before it and nothing else; a fix to the compiler
invalidates everything. Say which, in the row.

## Base discipline

**A branch is only as useful as its base.** Two of the rows below sit on Update
54 and are therefore not yet carried forward, however finished the work is.
Rebasing them is BOX cost we have to pay; leaving them is a cost we pay later
and with interest.

Check a base, never assume it:

    git merge-base <U55-commit> <branch>     # == U55 means based on U55

That check is why the ledger is trustworthy. `git log U55..branch` does NOT
answer it -- for a U54-based branch it happily lists that branch's own commits
and reads like an answer.

## The rows

Update 55 is `675a0775`, tag `u55`, seed `81F9E8171DCF6268`.

**Everything we own now lives on ONE branch: `NewRepository@u56-candidate`**
(worktree `cobblestone-u56`), cut from `u55` and nothing else. The per-fix
branches below are its sources; they stay, but the superset is what gets built,
tested and split into PRs.

### Carried onto u56-candidate

| Fix | Source branch | How it was carried | Proven |
|---|---|---|---|
| Four memory builtins + Nothing-returning fragments + address-of knows an enum | `u55-plus-memory-builtins` | cherry-pick, clean | refusal set at U55 drops to one (`T38`) |
| `real-to-int` / `real-from-int`, the f64 conversions | `zig-plug-real-bitcast` | cherry-pick, 4 conflicts resolved by keeping BOTH sides | U55 has no such emitter at all |
| `run.ps1` creates its output dir and falls back to the seed | `zig-plug-real-bitcast` | cherry-pick, clean | not absorbed by U55; checked by diffing the file |
| WGSL causes 1 and 3 | `wgsl-firefox` | cherry-pick, clean | naga 19/44 -> 41/44; eye-tested in Firefox |
| ZigEmitter split four ways | `zig-prelude-chapter` (U54) | **RE-RUN, not rebased** | 421 definitions in, 421 out, 0 duplicates |
| Four dead definitions deleted | `zig-prelude-chapter` (U54) | re-verified dead at U55, then re-deleted | no caller under codex/, apps/, docs/, build/ |

### NOT carried, deliberately

| Fix | Why |
|---|---|
| `real-to-bits` / `bits-to-real`, the f64 bitcasts | **U55 absorbed them.** Cherry-picking would have duplicated upstream's own work; the conflict at `ZigBuiltinEmitter` is what revealed it. |
| plugs-backlog rows | PR-shaping, not needed to build. U55 renumbered the file to 2.28 and rewrote 14,377 lines, so rows get written fresh against U55's numbering when the PRs are cut. |

### What Rust said before any box time

Run differentially against a plain `u55` worktree, because a whole-tree number
alone means nothing:

- `parsedump cover` -- **1959 parse errors both sides, 44 unstructured bodies
  both sides.** No regression. `TOO MANY LOOSE TOKENS` fires identically on
  plain U55, so it is a pre-existing whole-tree condition and not ours.
- `xref dangling` -- **1676 names both sides, set-identical.** Nothing new
  dangles, nothing stopped dangling.
- `xref bundle` on the zig plug -- **147 unresolved names both sides**, and the
  required-chapter list byte-identical. The split adds no cite requirement.
- Definition count reconciled exactly: 418 at U55, +5 memory builtins, +2
  conversions, -4 dead = **421**, matching `cohesion` across the four pages.
  0 duplicate names across the pages.
- **Rust also caught its own blindness:** `xref chapter` keyed on the FILE, so
  the four-page chapter reported 194 definitions and appeared to read itself.
  Fixed in `rust-codex-compiler@1777a2e` before trusting anything else it said.

## The fork that has to be settled first

Two ways to root the transpiler, and they lead to different supersets:

- **Cite the driver** (`u55-driver`). Kills harness drift permanently -- the
  drift that has now cost us the `lower-chapter` arity chase three Updates
  running AND `T38`, which is the same disease. Costs three more emitters in the
  superset, unless the reachability turns out to be narrow.
- **Keep the hand harness** (`u55-minimal`). Superset stays U55 + 4 commits.
  Costs a signature chase every Update, forever.

Settle it by measuring what a driver-citing entry actually reaches, not by
argument. Until it is settled, both branches stay.
