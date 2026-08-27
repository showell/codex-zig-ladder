# What the lambda-span fix does to the corpus

Transpile-stage census, 606 programs of `codex/test`, both sides through the
SAME plug -- only the compiler source differs (`native/codexir` built from the
u51 pin `012a9d2e` versus from `bba94d1b`). Baseline is the banked
`corpus/census.json`; the fix's run is `corpus-transpile-bba94d1b.log`.

    stage         u51 pin    lambda-span fix
    clean            318          324   (+6)
    markers          259          253   (-6)
    unresolved        16           16
    zigemit           13           13

**Six programs moved, all of them `markers -> clean`. Nothing moved the other
way, and no program gained a marker.**

    ir-check-clean              depot test
    linear-capture-once         depot test
    roc-closure-captures-list   our Roc port -- the program that raised H2
    roc-fold-count              our Roc port
    roc-fold-product            our Roc port
    roc-fold-sum                our Roc port

Every one of the six lost exactly one marker, and it is the same marker in all
six: **`no zig type for this codex type`**. That is the H2 marker -- the
emitter's `otherwise` floor reached because a parameter arrived as `ErrorTy`.

**For comparison, the deleted plug-side recovery moved four** (318 -> 322) and
cost 294 lines in `ZigEmitter.codex`. The compiler fix moves six and costs the
emitter nothing.

Caveat worth keeping: `native/codexir` is the compiler AS TRANSPILED BY THE
PLUG, so this is the plug grading its own homework at one remove. It is a
valid A/B because both arms use the identical plug, but it is not a trust
claim -- the bare-metal rungs are.

**A separate thing this run exposed: `corpus/transpile.json` is STALE.** It
holds 596 programs and no `zigemit` bucket, while its sibling
`corpus/census.json` holds 606 and has one. The two banked artifacts disagree
about the same corpus, and a diff taken against the wrong one is silently
wrong -- it read as 21 movers including six spurious regressions before the
mismatch was noticed. Not fixed here; recorded so the next reader does not
repeat it.

---

## The conformance answer, and how the full-corpus run nearly gave a false one

**The blast radius is SEVEN programs.** Of 577 emitted `.zig` files, **570 are
byte-identical** between the pin and the fix. Conformance cannot change for
those, by construction, so the whole conformance question reduces to seven.

Run on both sides, same corpus, same zig 0.16.0:

    pin 012a9d2e   7 programs: markers 7, 0 clean, nothing built
    fix bba94d1b   6 clean -> BUILT AND RAN -> match 6, and 1 still markers

    ir-check-clean              markers -> match
    linear-capture-once         markers -> match
    roc-closure-captures-list   markers -> match      the program that raised H2
    roc-fold-count              markers -> match
    roc-fold-product            markers -> match
    roc-fold-sum                markers -> match
    roc-fold-empty              markers -> markers    `no zig type for this codex type`

Six programs go from refusing to emit, to emitting zig that builds, runs, and
**matches its hand-verified `.expected`**. `roc-fold-empty` keeps one marker,
and it is a DIFFERENT defect: an empty list's element type, which no lambda
parameter fix reaches. **Zero regressions.**

## The instrument lied, and that is worth more than the result

The full-corpus `--run` reported `match 191, refused 112` against a bank of
`match 268, refused 24`, and printed **94 programs as `match -> refused`**. It
looked like a large regression from the fix. It was not. Checked three of the
flippers:

- `arithmetic`'s emitted zig is **byte-identical** between pin and fix, so the
  fix cannot have touched it;
- built by hand it compiles and prints the right answers;
- re-run through `corpus_run.py --run --only` in the FIX sandbox it is `match`.

The cause is in the ladder's own banked data. Committed `corpus/run.jsonl`
says `arithmetic refused` with a specific zig error; committed
`corpus/census.json` says `arithmetic verdict match`. **Two banked artifacts
contradict each other about the same program**, the resume carried the stale
one, and the diff was taken against the other. `corpus/transpile.json` is a
third: 596 programs and no `zigemit` bucket where `census.json` has 606 and
one.

The resume's own guard -- "carried from run.jsonl (emitted zig byte-identical,
toolchain unmoved)" -- reads a sha map from a banked artifact that is itself
stale, so it concludes byte-identical for programs it has no current sha for
and carries verdicts it should have dropped.

**Nothing here is fixed.** It is recorded because the corpus conformance
numbers this tree quotes -- `clean 318, match 268, refused 24` -- come from
these files, and at least one of the three is wrong about at least 94
programs. A number that cannot be reproduced by re-running the programs it
describes is not a measurement.
