# DEPRECATED

**This repository is retired as of 2026-09-04. Do not fix it, tidy it, or keep
it current.** The useful parts are moving to focused repos; whatever nobody
carries over dies here with it.

`PRIORITIES.md` is no longer the plan. It is a record of one.
`OLD_README.md` is what this file used to say.

> **FUTURE-CLAUDE: UPDATES ARE PROCESSED IN THE CLOUD NOW, NOT ON THE DROPLET.**
> Update 62 (2026-09-25) was the first processed entirely in a Claude Code
> cloud session, and that is the plan going forward. What that means:
>
> - **Nothing from the previous Update is lying around, on purpose.** No
>   `~/codexzig`, `~/codexir`, `~/zigemit`, `~/runs`, release worktree or
>   pinned checkout. Steve prefers it: stale assets from a prior Update cause
>   confusion, and everything is regenerable. Build what this Update needs,
>   from this Update's commit. Where an older log (U61 and before) says a
>   bundle "is kept" or points at a droplet path, that described the droplet.
> - **The container is fresh and its installs do not survive.** Install tools
>   reactively (see "From a cloud session" below); there is no setup script
>   by choice.
> - **Only codex-zig-ladder is cloned at start.** Add the sibling repos to the
>   session as the Update reaches them. The app can only show files under
>   this repo and the scratchpad, so put a diff of any sibling-repo change in
>   the scratchpad for Steve to read.
> - **Push as you go.** The container is reclaimed when idle; what is not
>   pushed is gone.
>
> `U62.log` is the worked example, including the order things were built in.

## Where the work went, and how the pieces relate

This repository is retired, but its README, its `U<NN>.log` files and its
Claude memory are still the index for every Cobblestone-related repo here.
Start at this table.

**Four coordinates locate any piece of work.** Naming all four is how you avoid
comparing two things that were never comparable.

| axis | values |
|---|---|
| **toolchain** | Rust · Zig · Wasm · QEMU (bare metal) |
| **subject** | fib · curated 28 · safari · the compiler itself (self-host) |
| **version** | a released Update (U56 = `6cd2ca1b`) · a candidate branch (`u57-candidate`) |
| **layer** | frontend (lex, parse, desugar, check, lower) → IR → plug → binary |

### Toolchains — two directions of attack

**Rust tests the system from the OUTSIDE IN.** `rust-codex-compiler` is an
independent reimplementation of the frontend, so it can disagree with upstream
about the IR. It is the only arm that can see a defect ABOVE the IR, because it
does not inherit upstream's frontend.

**Zig and Wasm test the system from the INSIDE OUT.** Both run Damian's own
frontend and check what comes out the back: each transpiles the compiler's own
source and must emit the same bytes for it twice — under QEMU and as the binary
that emitted it. A fixed point says the whole frontend plus the whole emitter
agree with themselves on the largest subject available. It cannot see a
frontend defect, because both of its passes inherit the same frontend.

**QEMU is the ground truth under both.** `cobblestone-qemu` runs Codex on real
x86 with no host runtime, which is the only place `address-of`, boxing, the
deck and memory are real rather than modelled.

| repo | toolchain | what it proves |
|---|---|---|
| [`rust-codex-compiler`](../rust-codex-compiler) | Rust | an independent frontend: `.codex` in, Codex IR out, graded byte-for-byte against `codexir`; plus an interpreter that sees MEANING rather than shape |
| [`codex-zig-transpiler`](../codex-zig-transpiler) | Zig | the fixed point, and the `codexir`/`codexcheck` oracles the Rust arm is graded against |
| [`codex-wasm-transpiler`](../codex-wasm-transpiler) | Wasm | the same fixed point through a second plug, which is what makes a shared-component defect visible |
| [`cobblestone-qemu`](../cobblestone-qemu) | QEMU | run Codex on real x86 and tell me what came out |

### Subjects — what gets compiled

A subject is not a toolchain. The same subject run through two toolchains is
the comparison that finds things; the same toolchain run on two subjects is
coverage.

| repo | subject |
|---|---|
| [`cobblestone-curated-tests`](../cobblestone-curated-tests) | 28 resolved units with upstream's own expected output, citing nothing — no `CODEX_ROOT`, no quire registry |
| [`safari-codex`](../safari-codex) | a real application, four arms on one source |

`fib` lives in `cobblestone-qemu` because it cites nothing and needs no
bundler, which is what makes it the transport smoke test. The compiler's own
source is the largest subject there is, and it is what the fixed point uses.

The **Firefox arm** is the WGSL kernels, graded by `naga` — Firefox's own WGSL
front end, run offline; Chrome's Tint is the permissive one, so a kernel Tint
accepts and naga rejects is a shader Firefox rejects. It lives in
[`cobblestone-qemu/wgsl/`](../cobblestone-qemu/wgsl): `check.sh` gates every
committed kernel in a second, `regen.sh` rebuilds a stale one from the
checkout's own plug under QEMU, and `serve.sh` is the tunnelled eye test. Its
README has the tunnel command and the rest.

### Reading a claim

"The fixed point holds" is a claim about **Zig · the compiler itself ·
u57-candidate · frontend-through-plug**. It says nothing about Rust, nothing
about safari, and nothing about U56 as released — where it does NOT hold.
Every one of those four is load-bearing.

## Processing a new Update

Each Update gets a `U<NN>.log` here. Every Update is a little different, so
this is the usual shape, not a checklist; the previous log is the best guide.

1. **Header.** Upstream is `damiant3/Cobblestone`. It has no tags and no GitHub
   releases: an Update is one squashed commit on `master`, and its notes are
   `docs/PM/Active/GitHubUpdates/GitHubUpdate<NN>.md` in that commit. The seed
   name is the first 16 hex digits, uppercased, of the sha256 of
   `seed/Codex.cdx`; check it for both the new and the previous Update.
2. **What upstream did with ours.** `u<NN>-candidate` is the previous Update
   plus our PRs. Upstream's `refs/pull/<N>/head` are fetchable, so the PR
   heads can stand in for the candidate. Compare file by file:
   byte-identical, prose only, code changed, dropped. **Check prose
   separately**: upstream often takes a PR with its comments edited or
   deleted, and "the code landed" does not say whether they did. When a file
   moved for other reasons too, `git apply --check -R` of the PR's diff says
   whether the PR's hunks are there as sent.
3. **`cobblestone-qemu`**, `run_all.py` with `CODEX_ROOT` at the Update's
   commit. GREEN is 5/5.

Then whatever the Update touches: the curated tests, the Rust gates, safari,
the transpilers' fixed points. The verdict closes the log.

**New chapter dependencies are where Updates get confusing.** If an Update
makes us edit our own chapter lists or harnesses to keep up, that is a smell:
first read how upstream changed its side (`build/compiler-order.txt`,
`codex/plugs/*/build.ps1`, `plug-build-lib.ps1`, `opening.codex`), then
derive from their files rather than add rows to ours. U62 is the worked
example: `cobblestone-qemu` `9ab698a`.

Branches: the showell-owned repos take fixes straight to their default branch.
That is `master` almost everywhere, but not everywhere
(`cobblestone-curated-tests` is `main`), so read it before pushing:
`git ls-remote --symref origin HEAD`. Guessing wrong once created a stray
`main` on cobblestone-qemu. Our Cobblestone fork is the exception, where work
goes on non-master branches.

**From a cloud session** (a fresh container, no droplet): only this repo is
cloned; add the sibling repos to the session. `cobblestone-qemu` needs
`qemu-system-x86`, `pwsh` (apt, after Microsoft's `packages-microsoft-prod.deb`)
and zig 0.16.0. The environment's network policy denies ziglang.org (a 403
from the session's own proxy, not from ziglang.org), but PyPI's
`ziglang==0.16.0` is the same build: link its package directory to
`~/zig-0.16.0`. Nothing installed survives the session; install reactively. `build.sh` looks for
pwsh at `~/.local/pwsh/pwsh`, so set `PWSH=$(command -v pwsh)`, or link it there,
which codex-zig-transpiler's `build.py` needs (it has no override). That one
also wants `zig` on PATH: `export PATH=~/zig-0.16.0:$PATH`.
rust-codex-compiler needs rustc 1.98 (the container had 1.94): `rustup
toolchain install 1.98`, then `CARGO_TARGET_DIR=~/build/rust-target cargo +1.98
build --release`. Curated's `~/codexir` bundle must include
`codexir-subject.codex` for `ir-interp`.
codex-wasm-transpiler needs `npm ci` in `tools/`; curated's `run-wasm` finds it
through `CODEXWASM=<its checkout>`. A depth-1 Cobblestone clone makes git
abbreviate to 7 characters where full history gave 8 (`3eac167` vs
`9fff850c`); anything that insists on 8 reads a receipt as missing. There is no
KVM, which does not matter: the harness defaults to `tcg`, which is what the
droplet timings were measured on.

Still here and not yet carried: `findings/` and `outbound/` — 344 of this
repo's 521 tracked files, the accumulated register of what we found in Damian's
compiler and what we sent him. That is a record with no machinery attached and
it deserves a home; it has not got one yet.

## Why it is being retired

Each of the repos above can be described in a phrase. This one could not. It was
a rung harness, a QEMU driver, a sandbox system, a findings register, an outbound
PR queue, a corpus census, a branch-topology ledger and three linters.

**And it was structurally unable to find a whole class of defect.** Its two arms
— bare metal and the zig plug — are both Damian's front end. They share the
lexer, parser, desugarer, checker and lowering, and diverge only at the emitter.
So anything wrong above the IR is invisible to it *by construction*, because both
arms inherit it identically. That is not a gap in coverage; it is a property of
the design.

The proof arrived on the day it was retired. Codex converts a decimal `Real`
literal incorrectly — 10 of 120 ordinary doubles land one ULP away, in the front
end, so every backend gets the same wrong bits. Fourteen rungs never saw it and
never could. An independent front end found it in fifteen minutes.

The long version is
[an essay](http://143.244.172.148:9100/notes/what-the-ladder-is-for.md).

## What was worth keeping, and is

The **progression** — a ladder works because a failure at rung N tells you rung
N−1 was fine, so you climb cheapest-first and the first red names its own layer.
Fourteen rungs was that idea with every historical frontier still nailed to it;
four layers is the same idea usable:

1. the text survives · 2. the meaning survives · 3. the IR survives · 4. the
machine survives

And the **QEMU knowledge** — the ring protocol, the gdbstub write-position
injection, the stall at exactly `RING_SIZE` that fires spuriously, the memory
bounds added after an emitted binary livelocked the host twice. Months of ouches
encoded as guards. That is in `cobblestone-qemu` now, and it was always the expensive
part; the rungs were the cheap enumeration on top of it.
