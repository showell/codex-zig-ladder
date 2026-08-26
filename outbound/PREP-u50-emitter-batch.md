# Prep: the outbound batch for 2026-08-26's verified work

Not a draft to send. This is the plan plus the backlog rows, prepared
while the `f17-f54` chain finishes so that sending is mechanical once its
sweep reports.

## The base, checked rather than assumed

`git fetch upstream` at 22:45 — **`upstream/master` is still `8cc80685`**,
the Update 50 release. Their tonight's landings (the three-plug Boolean
fix) are on their internal main and are NOT public yet.

Consequences:

- The branch cuts from `8cc80685`, in a throwaway worktree, per the
  ladder README's checkout model.
- **Our finding-52 commit will duplicate work they have already done.**
  They told us they fixed it in their copy of the zig plug. Ours is not
  identical — ours guards `TextTy`, so a Text literal pattern spelled
  `"True"` is left alone — and theirs may not. The PR must say this
  plainly and let them take whichever they prefer rather than pretending
  we did not know.
- The stack under this branch is EMPTY (all eight prior PRs landed in
  Update 50), so the measurements are against the bare release. Name that
  in the PR, per the standing rule.

## What goes in, and what does not

**IN — built, measured, sweep green:**

| commit(s) | finding | measured by |
|---|---|---|
| `a961dcb6` `d6a5782b` | tvar recovery | rows 1.84/1.85, already drafted in-tree |
| `bbf339c0` `8b493672` `d4ba6e75` `419c292d` | 47, the scope guard | `f47-guard2`, tvar markers 40 → 0 |
| `6bf2911c` | 51, refusal strands its parameters | `f52-f53` leg1 GREEN, three Roc ports |
| `8b641203` `31be533e` | 50, `show`'s five type cases | `f52-f53`, 41 bool refusals gone |
| `a2d4646c` | 52, Boolean literal patterns | `f52-f53`, both pinned programs match |
| `3b7cc358` | 53, thread entry returning a value | `f52-f53`, 0 startFn refusals, match +38 |
| `05b6adb4` | 17(A), units are their backing type | `f17-f54`, 6 programs, **sweep pending** |

Plus the Roc port test programs that pin 50 and 51, which are oracles
written by people who have never seen this emitter.

**OUT — not verified, or not worth sending:**

- `3f0f42e5` `1c35e1de` — the H2 recovery rule. Never built, and it
  carries a known gap recorded in its own prose (match binders are not
  guarded against rebinding).
- `7de07cf0` — units part B. Written an hour ago, never built.
- `cab52a35` — the two prelude renames. **Correct but fixes nothing
  measurable**: the class is 66 names and this is four of them, and the
  chain proved it by moving the error to the next shadow of the same
  name. Send the ROW, not the commit. A partial rename that moves no
  program is noise in a PR.
- Finding 56 (their type checker) — **blocked on the control probe.** If
  the control also compiles clean, the claim changes shape. Nothing about
  it goes out until that runs.

## Drafted rows

### 1.85 — the completion

Row 1.85 already sits in the tree ending with what it owed:

> **What is owed before this row is worth sending:** the last-resort rule
> needs a scope test -- keep a variable answer only where the emission
> site declares it -- and then `corpus_run.py --run` over the corpus,
> which BUILDS what it transpiles, rather than a marker census.

Both are done and the row can close. Append:

**PAID, 2026-08-26.** The last-resort rule now carries the scope test the
row asked for: `emit-zig-type` takes the set of type variables the
emission site actually declares as `comptime T<n>` parameters, and
refuses at the OUTERMOST type when a variable is not in it — outermost
because `zig-is-unmapped` tests a leading prefix, so a marker buried
inside `*CxList(...)` is invisible to it. Measured by `corpus_run.py
--run`, which builds and runs rather than counting markers:

    tvar markers   40 -> 8 -> 0 over 606 programs
    corpus match   183 -> 185, nothing that matched stopped matching
    sweep          14/14

**The first write-up of this said "verified, clears all forty" and used
the wrong metric.** A marker count is the emitter's self-report about
itself. Three programs had traded a diagnostic for a build failure and
the count could not see it.

### 1.86 — a refusal strands the parameters it consumed

**1.86 -- FIXED, a refusal that replaces an expression kills the
parameters that fed it, and zig reports the stranding instead of the
refusal.** (Steve Howell, 2026-08-26; `codex/plugs/zig/`.)

The scope test in 1.85 turned `use of undeclared identifier 'T16'` into a
sentence naming the variable and the callee. Zig never printed the
sentence. The refusal consumed the only expression reading a parameter,
so the parameter went dead, and zig's unused-parameter check runs against
the signature before the `@compileError` in the body is analysed.

Measured on four programs, with zig's own column landing on the stranded
parameter each time:

    roc-iter-map      857:68   transform: CxFn1(T44, T45)
    roc-iter-keep-if  857:52   pred: CxFn1(T44, bool)
    roc-iter-drop-if  857:52   pred: CxFn1(T44, bool)
    probe-tvar-recovery  908   wrap_int(n: i64)

`roc-iter-map` strands `transform` and leaves `it` alone, because `it`
still has a reader.

**The mechanism was a liveness question asked of the wrong artifact.**
`emit-zig-param-discards` asks `zig-occurs` about the IR body — right
everywhere the emitter answers, wrong exactly where it refuses, since the
IR still uses the parameter and the emitted zig does not. A refused body
now discards every parameter. Not the ones a name search calls dead:
`_ = x;` beside a live use is legal zig, and a substring test on
parameter names is a collision this tree has been bitten by.

### 1.87 — `show` implements one of five type cases

**1.87 -- FIXED, `show` dispatches five ways on the argument's type and
the zig plug implemented one arm for all five.** (Steve Howell,
2026-08-26; `codex/plugs/zig/`.)

`show : forall a. a -> Text` (`Types/Builtins.codex:69`). Bare metal
picks by the argument's type (`Emit/X86_64.codex:1652`): f32 real widens
before `__real_to_text`, other reals go straight there, `TextTy` is the
expression itself, `BooleanTy` is `emit-show-bool`, everything else is
`__itoa`. The plug emitted `cx_show_int` for all five.

**42 of 113 corpus refusals — the largest single class.** 40 were
`expected type 'i64', found 'bool'` and 2 `found 'f64'`. The site was
read at the call in three of the forty rather than inferred from the
message.

Fixed for Text and Boolean; the unit wrapper comes off first for the
reason bare metal records. `True`/`False` are built through the emitter's
own text escaper rather than hand-encoded, so their CCE bytes come from
the same place every other literal's do. **Reals refuse with a named
marker rather than guess** — `__real_to_text` is hand-written assembly
(sign bit, `cvttsd2si` integer part, fifteen fractional-digit iterations,
CCE digit offsets) and `std.fmt` would agree with it on some values and
not others.

Found by a Roc port on its first run.

### 1.88 — the thread entry cannot return a value

**1.88 -- FIXED, emitted `main` spawns `opening` directly and zig refuses
a thread entry that returns a value; 40 corpus programs.** (Steve Howell,
2026-08-26; `codex/plugs/zig/`.)

Every emitted program runs its entry on a thread for the 512 MB stack —
the same workaround the C# plug carries, for the reason it records (the
lexer's mutual recursion overflows 1 MB). Zig requires that entry to
return `u8`, `noreturn`, `!noreturn`, `void` or `!void`. 40 subjects
declare `opening` returning a value and all 40 failed inside
`std/Thread.zig` before a line of their own code was analysed.

**The value is the program's OUTPUT, not a status.** `ble-att-encode`
ends `in a + b + c + d + e` and its `.expected` is `5`. A shim that
discarded it would trade 40 loud refusals for 40 silent mismatches.

`cx_entry` is a void shim that prints, dispatching on the CODEX type arm
for arm against `emit-opening-result-print`
(`Emit/X86_64Chapter.codex:222`). An earlier draft dispatched on the
plug's own rendered zig type text and was wrong twice over: Boolean and
Char both render to something that is neither `void` nor `[]const u8`,
so a Boolean entry would have re-created 1.87 at a new site and a
Character entry would have printed a number where bare metal prints
nothing. **Caught by a cold read before it was built.**

Note for the record: `opening-call-text` in the C# plug DISCARDS an
effectful `opening`'s value. Bare metal peels the effect and prints, and
the depot agrees — `gpu-ptx` and `gpu-doorbell` declare
`opening : [Console] Integer` and their `.expected` files end with the
bare `0` that print produces. We followed bare metal.

### 1.89 — unit families

**1.89 -- FIXED (half), a unit family was mapped to `void`, erasing the
payload while the arithmetic around it stayed correct.** (Steve Howell,
2026-08-26; `codex/plugs/zig/`.)

`Length = unit family Millimeter` with scale factors; a `Length` value IS
its base-unit integer. `emit-zig-type` mapped every `UnitTy` to `void`.

`unit-family`'s emitted body already computed all four of its expected
answers — scale factors multiplying, conversions inlined to `@divTrunc`,
`double-length (Millimeter 50)` constant-folded — and then failed to
compile because the values were typed `void`:

    fn Centimeter(__fv: i64) void {          <- void, should be i64
        return b0: { const __unit_0 = (__fv *% 10); break :b0 __unit_0; };
    }

Three arms move: `emit-zig-type` recurses into the backing type,
`zig-let-annot` peels too, and the entry shim recurses rather than
assuming `void`. Six programs, no regressions.

**NOT fixed and reported here as open:** a record FIELD typed by a unit
family arrives as an `ATypeExpr` and takes `emit-zig-atype`, whose
`ANamedType` arm emits any unrecognized name verbatim
(`ZigEmitter.codex:445-447`) — `ob_sample_rate: Frequency,` against a zig
that has never heard of `Frequency`. 11 more programs. **That same
`else` also emits a source-level TYPE VARIABLE verbatim** (`queue-test`:
`QueueS(T52){ .front = cx_ll_empty(a), ... }`, where the definition
declares `comptime T52` and the field's element type is spelled `a` in
the same expression), and that path takes no scope and has no refusal, so
every guard from 1.85 walks straight past it.

### 1.90 — the prelude's locals are undeclared reserved words (DOC ONLY)

**1.90 -- OPEN, the zig plug's runtime prelude shadows user top-level
names with its own locals and parameters, and nothing says so.** (Steve
Howell, 2026-08-26; `codex/plugs/zig/`.)

Zig forbids a local shadowing a container-level declaration, so every
identifier the prelude uses privately is a reserved word for every Codex
program the plug compiles.

    dns-answer-count.zig:26:15  function parameter shadows declaration of 'l'
    tcp-checksum-refuse.zig     function parameter shadows declaration of 'base'

against user top-levels `fn l()` and `fn base()`.

**The surface is 66 names**, extracted from the prelude of an emitted
program — 47 `const`/`var` bindings and 33 parameters. It includes `x`,
`y`, `d`, `e`, `i`, `n`, `s`, `len`, `ctx`, `a`, `hi`, `lo`, `acc`,
`buf`, `out`, `top`, `start`, `code`, `path`. **A Codex program defining
a top-level `x` cannot be compiled by this plug.**

The plug guards user names against prelude DECLARATIONS
(`zig-prelude-decls`) and not against prelude locals.

**Reported without a fix, deliberately.** Two candidate fixes and both
are larger than they look. Adding the 66 names to `zig-prelude-decls`
renames `i`, `n` and `s` through all 55 `zig-sanitize` call sites — type
names, constructor names, parameters, definitions — which is a large
blast radius through rename machinery to buy two programs. Renaming the
prelude's own 66 identifiers is correct and confined, but it is a rewrite
over 931 lines of zig embedded in Codex string literals where a subtle
miss breaks every emitted program. A first attempt renamed four of them
and the chain proved it insufficient by moving the error to the next
shadow of the same name — which is also how we learned the first
measurement had counted only `const`/`var` and missed every parameter.

## PR body skeleton

- One paragraph: what the branch is, cut from `8cc80685`, **stack empty**
  so the measurements are against the bare release.
- The corpus number as the headline: **`match 183 -> 269`, `refused 112
  -> 24`**, six legs green on every chain, sweep 14/14 throughout.
- Per-finding: row number, one sentence, the measurement.
- The finding-52 duplication, stated up front.
- What we are NOT sending and why (the recovery rule, units part B, the
  prelude rename) — three sentences, so the absence is deliberate rather
  than an oversight.
- `Ladder:` line naming the tag.

## Still to do before sending

1. `f17-f54` sweep must report 14/14. Units part A is in the batch and
   its sweep is the leg that would catch a unit value whose printed
   answer moved.
2. Cut the worktree off `8cc80685`, cherry-pick the IN list, confirm it
   builds there — the branch is a different tree from the one measured.
3. Cold-read the PR artifact before it goes. That read has caught a false
   headline claim, a reproducer that could not reproduce, an unverified
   negative, and a citation off by two lines. It is not optional.
