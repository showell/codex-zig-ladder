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
