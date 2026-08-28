# PR body draft — zig plug: emit the prelude last

Branch `prelude-last`, rebased clean onto `968d4600` (Update 52) with no
stack under it.

**On the base, stated narrowly:** Update 52 does not touch
`codex/plugs/zig/` -- zero lines -- and the rebase was clean. That is all we
claim about it. The measurements below were taken against emitted output from
an earlier toolchain and have not been re-taken at this base; U52's compiler
changes could change what the plug emits. It does not affect what is being
graded, because "does zig care where the prelude sits" is a property of zig
and of the file's shape rather than of which Update produced the file. The
byte counts are the exception and are keyed to the files actually measured.

`Ladder: postlude-corpus-589`

---

## What it changes

`emit-zig-chapter` emitted

```
zig-prelude & types-text & defs-text & zig-main ...
```

so every file the zig plug produces opens with **37,409 bytes — 813 lines —
of fixed runtime support**, byte-identical in all of them, and the transpiled
program starts at line 840. Reversed:

```
types-text & defs-text & zig-main ... & zig-postlude-banner & zig-prelude
```

The program comes first; the prelude follows it behind a banner that says
what is below the line and why.

Zig does not order declarations at container scope, so this is inert.

## Why, beyond readability

- A diff between two emitted programs now opens on **what differs**, instead
  of on hundreds of identical prelude lines.
- The arbitrary transpiled code — which is where bugs are — is what a reader
  meets first. The prelude is fixed text that is the same in every file.
- The proportion is worse than it sounds. In the plug's 589-program corpus
  the *smallest* emitted program is 38,219 bytes of which 37,409 is prelude:
  **the program is 2% of its own file.**

`zig-postlude-banner` lives at the concatenation site rather than inside
`zig-prelude`, because placement is `emit-zig-chapter`'s concern and because
`build/check-zig-prelude-surface.ps1` derives its reserved-name list from
`zig-prelude` and should not have to read past a comment to do it.

## Evidence

All 589 already-emitted corpus programs were transformed -- prelude moved
below the program, banner inserted -- and both variants of each were compiled
and run. Full log in `outbound/MEASURED-prelude-last.log`.

```
programs graded          589
build outcome agrees     589
of which built           202
zig diagnostics agree    589
ran both ways            202
output byte-identical    198
identical but for source positions in a panic backtrace     4
disagreements              0
```

The four are bounds-check programs whose panic prints a backtrace naming
source positions, which the move shifts by construction. Same exit status,
same stdout, same panic message, and the same machine addresses in the trace.

### And the compiler itself

No corpus program resembles these in size -- 4.6 MB against a 42 KB median.
Built both ways, then DRIVEN: each native reads Codex on stdin and answers on
stderr, and the input was produced once and handed to both builds.

```
zigemit     445,173 bytes   exit 0, 42,547 bytes out, byte-identical: YES
codexir   1,924,806 bytes   exit 0, 18,350 bytes out, byte-identical: YES
codexzig  2,276,581 bytes   exit 0, 41,596 bytes out, byte-identical: YES
```

### How this was graded without building the plug

The change is a pure text reordering, so the reordering was done outside the
plug and then PROVED to be the plug's: it reproduces the plug's own
before/after pair for the `arith` sample byte for byte (40,941 -> 41,661,
delta 720, all banner), taken from `codex-zig-transpiler`'s history at
`8595322` and `daf36cf`. With that calibration, grading the transform over the
corpus is grading the plug, and no two native builds and two transpiles were
needed to say so.

### The repair it carries, which it caused

`build/check-zig-prelude-surface.ps1` derived the prelude as the line-wise
common PREFIX of several emitted programs. With the prelude last that prefix
is the emitted tuple types -- and the check does not fail, it reports a
smaller surface and passes:

```
[zig-prelude-surface] prelude 24 lines over 4 programs; surface 5 names; zig-prelude-decls carries 101
[zig-prelude-surface] OK: every derived name is reserved.
```

Five names checked where the real surface is 98, all five already reserved,
exit 0. Not a refusal -- a green light over a check that had stopped looking.
Anchored on the banner instead, and the subjects' preludes are now REQUIRED to
agree rather than silently truncated to whatever they happen to share. It
derives 97 where the prefix scan derived 98; the one it drops is `d`, which
was never a prelude name -- the prefix ran past the prelude into `Tup4`'s
comptime parameters and picked it up by accident.

The prose above `zig-prelude-decls` described that same prefix derivation and
is repointed. It also now states the rule the list has always followed
implicitly: it is the UNION over the whole prelude, and must stay that way
even if the plug someday emits only the parts a program reaches -- otherwise
the spelling of a user's local starts depending on which builtins the program
happened to touch.

We swept the rest of the tree for the same assumption. `check-zig-prelude-surface.ps1`
is the only positional dependency: `plug-oracle-test.ps1`, `check-plug-guards.ps1`,
`check-plug-builtins.ps1` and `quire-map.ps1` mention a prelude only in prose
or about other plugs.

### Every byte of the transpiler's output accounted for

`codex-zig-transpiler` transpiles the Codex compiler through this plug, so it
emits the change *and is changed by it*. Its emitted zig grew 3,870 bytes,
and the growth is exactly three things:

| | bytes |
|---|---|
| the banner, emitted into the file | 720 |
| `fn zig_postlude_banner()` — the new constant, transpiled | 3,116 |
| `fn emit_zig_chapter()` — the reordered concatenation | 34 |
| | **3,870** |

Checked rather than inferred: undo those three differences in the 2,387,634-byte
after-file and it is **byte-identical** to the before-file, with the prelude
back on top. Nothing else in 2.3 MB moved.

The fixed point holds at this revision — the transpiler still re-emits its own
bundle byte-identically — and the `arith` sample transpiles, builds, runs and
matches all nine lines of its expected output.

## What this is not

It is not a fix for anything. Nothing was wrong; the file was just upside
down for a reader. It is also the small half of a larger idea we are costing
out separately: **nothing uses the whole prelude.** The greediest program in
the corpus uses 55 of its 93 top-level declarations and the median far fewer,
so most of those 37 KB could be dropped per program rather than merely moved.
Moving it first is worth doing on its own, and it makes the shaking change a
one-line edit at the same seam.

Renumber the backlog row freely if `1.99` collides with anything in flight.
