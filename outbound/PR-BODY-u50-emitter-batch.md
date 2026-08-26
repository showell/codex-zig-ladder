# PR body draft — zig-plug-u50-emitter-batch

Paste as the PR description. Branch cuts from `8cc80685` (Update 50).

---

Six defects in the zig plug, found and fixed on 2026-08-26, plus two
reported open. Cut from Update 50 with **no stack under it** — all eight
prior PRs landed in that release, so every measurement below is against
the bare release rather than against a patched tree.

**Headline, from `corpus_run.py --run`, which builds and runs each
program and diffs against its `.expected` rather than counting markers:**

```
corpus match      183  ->  269
corpus refused    112  ->   24
ast/allcycles.sh  14/14 on every chain, final sweep 23:05
```

Four verification chains, six legs each (natives, a type-variable case
matrix, the corpus, the `codexzig` self-emission fixed point, eleven
ported Roc snippets, and the bare-metal sweep). Green throughout.

## What is in it

| row | defect | reach |
|---|---|---|
| 1.85 | the type-variable scope test this row asked for, and its measurement | markers 40 → 0 |
| 1.86 | a refusal strands the parameters it consumed; zig reports the stranding, not the refusal | 4 programs |
| 1.87 | `show` dispatches five ways on the argument's type; the plug implemented one arm for all five | 42 of 113 refusals |
| 1.88 | emitted `main` spawns `opening` directly and zig refuses a thread entry returning a value | 40 programs |
| 1.89 | a unit family was mapped to `void`, erasing the payload | 6 programs, 11 more open |
| 1.90 | the prelude's own locals and parameters shadow user top-level names | 66 reserved names — **open** |

Also included: eleven test programs ported from Roc's evaluator suite,
carrying Roc's own expected values. They are oracles written by people
who have never seen this emitter, and two of the six defects above were
found by them rather than by the corpus — including 1.87, which had been
sitting in our own corpus output as its largest single refusal class for
as long as the corpus has existed.

## Two things you should know before reading the diff

**1.87's Boolean fix duplicates work you have already done.** You told us
on 2026-08-26 that you had fixed the Boolean literal-pattern class in
three plugs including your copy of this one. `upstream/master` was still
`8cc80685` when this branch was cut, so the commit is here. Ours guards
`TextTy` — a Text literal pattern spelled `"True"` is left alone — which
yours may or may not. Take whichever you prefer; we would rather flag the
overlap than have you find it in a conflict.

**1.90 ships a change that fixes nothing, on purpose.** It renames four
prelude locals. The two programs it targets still refuse, because the
rename moved the error to a function parameter of the same name. It is
included because it is exactly what was measured, and because measuring
it is how we learned the class is 66 names rather than the 45 we first
counted — our first extraction searched `const` and `var` and never
looked at parameters. The row costs both candidate real fixes and takes
neither.

## What is deliberately NOT in it

Three changes written the same day and left out for cause:

- **A lambda type-recovery rule.** Written, never built, and it carries a
  known gap recorded in its own prose: it guards `let` and nested-lambda
  rebinding but not match-branch binders, so a binder sharing a
  parameter's name would be read as evidence about the parameter. That
  produces a wrong recovered type rather than a refusal, which is the bad
  direction.
- **The other half of 1.89** — declaring unit families so
  `emit-zig-atype`'s verbatim name becomes correct. Written an hour
  before this branch, never built.
- **The 1.90 class fix.** Not written.

## Method note

Every fix here carries a prediction written into the finding *before* the
build that tested it. Two of five were wrong, and both wrong ones are
recorded in the rows rather than quietly dropped — 1.88's predicted a
wave of newly-visible failures behind the 40 it unblocked and got two,
and 1.90's predicted two programs would start passing and they did not,
which is how the 66-name surface surfaced at all.

Ladder: `u50-emitter-batch`
