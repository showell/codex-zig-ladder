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

## Fixed, and the bank is VINDICATED

Both halves repaired the same afternoon (`7567bf0`, `2b60551`): every verdict
line now carries its own cache key so the resume cannot be lied to, the stage
outputs are untracked because only a bank should be tracked, and a bank diff
now says out loud when the bank was taken with different natives than the ones
in `native/`.

Then the bank was rebuilt from scratch to find out whether it had been
contaminated too -- a full `--run --bank` at the pin with NO journal to resume
from, **all 318 clean programs actually built and run**, natives whose shas
already matched the bank's `meta.tools`:

    606 programs: clean 318, markers 259, unresolved 16, zigemit 13
    match 268, refused 24, no-expected 23, hardware-only 2, crashed 1

**The result is BYTE-IDENTICAL to the committed `census.json`.** Zero rows
changed their answer, zero `zig_sha` differ, same 606 programs. So the number
this tree quotes everywhere -- `clean 318, match 268, refused 24` -- is
correct and is now independently reproduced without a single carried verdict.

The rot was confined to the two stale stage outputs. The bank was honest the
whole time, which is exactly what a bank taken deliberately is supposed to be,
and is the argument for the split that now exists.
