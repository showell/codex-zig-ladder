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

Update 55 is `675a0775`, seed `81F9E8171DCF6268`.

### ON U55 -- carried forward

| Fix | Lives on | Proven | Destined | Invalidates |
|---|---|---|---|---|
| Four memory builtins: `peek-32`, `poke-32`, `alloc-bytes`, `poke-byte`, `__memset`; Nothing-returning fragments return void; address-of knows an enum | `NewRepository@u55-plus-memory-builtins` (worktree `cobblestone-u55min`), 4 commits on U55 | Refusal set at U55 drops to exactly ONE (`T38`) | U56, as the U55 rebasing of plugs-backlog 2.19 | every zig-arm result |
| WGSL causes 1 and 3: loop-helper returns a typed zero; `f32` literals emit as hex constant expressions, and refuse above `e == 255` | `NewRepository@wgsl-firefox` (worktree `cobblestone-wgsl`), 2 commits on U55 | naga 19/44 -> 41/44 by simulation; eye-tested in Firefox | U56, as a PR with the gate | wgsl arm only |
| `lower-chapter` takes 11 parameters and returns a tuple at U55 | `codex-zig-transpiler@u55-minimal` | The transpiler reaches emission; only `T38` refuses | ours, not upstream's | transpiler only |
| `zigc` CALLS the driver instead of copying it | `codex-zig-ladder@master` | The rung bundles `Chapter: Opening`; harness went 10 KB -> 1.1 KB | ours | zigc rung only |
| The same conversion for the transpiler | `codex-zig-transpiler@u55-driver` (`8541c14`) | Compiles; costs three more builtins (see OPEN) | ours | transpiler only |

### ON U54 -- STRANDED, not yet carried forward

| Fix | Lives on | Why it is stuck |
|---|---|---|
| `ZigEmitter.codex` split four ways (2555/1049/513/564 lines) + 4 dead definitions deleted | `NewRepository@zig-prelude-chapter` (worktree `cobblestone-outbound54`), 4 commits on U54 | Needs rebasing onto U55. U55 touched `ZigEmitter.codex` (20 lines), so this will conflict, and the split must be re-cut against U55's text. |
| plugs-backlog row 2.19, the PR-shaped version of the memory builtins | `NewRepository@zig-plug-memory-builtins`, 5 commits on U54 | Its four code commits ARE carried forward above. Only the backlog row is stranded -- it conflicts on U55's renumbering of `plugs-backlog.md`. |

### OPEN -- known, unfixed

| Issue | Where it bites | What is known |
|---|---|---|
| `T38` | `codex-zig-transpiler`, the one remaining refusal at U55+4 | PRE-EXISTING, not U55 damage (U54 `__lam_436`, U55 `__lam_443`), and OURS: the harness maps over `(cr.env).bindings`, a two-level field access the emitter cannot type. The driver sorts first and resolves once. The proof is two lines below in our own output, where `map_list(TypeBinding, TypeBinding, ...)` over `sort-bindings` emits cleanly. |
| WGSL cause 2 | `cobblestone-wgsl` | INCOMPLETE and known to be so. Helpers are emitted by `wgsl-topo-pass` at MODULE level where `ctx.kprefix` is `""`, so keeping the prefix keeps nothing: the signature loses the parameter and the body still writes `(*tex)[ti]`. Needs an owner-prefix per helper via the `wgsl-reachable` walk. |
| Driver-citing enlarges the plug surface | the fork below | A subject carrying `Chapter: Opening` reaches serial, device and x86-64 code, so the zig plug owes `port-out-byte` (`opening.codex:343`), `poke-16` and `__self-type-defs`. Measured 2026-09-03: four refused builtin kinds becomes seven. NOT yet established whether those are genuinely reachable from a driver-citing entry or an artifact of wider-than-necessary reachability -- `port-out-byte` appears exactly once, which smells narrow. |
| U55's `.sources` sidecar digests the empty set | our bundles | `Get-PlugSourceDigest` globs `*.codex` in the plug dir; the ladder assembles a synthetic plug whose dir holds none. Nothing in our flow reads it, so it is gitignored, not fixed. |

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
