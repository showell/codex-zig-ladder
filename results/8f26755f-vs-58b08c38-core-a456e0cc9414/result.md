# 8f26755f-vs-58b08c38-core-a456e0cc9414

**8f26755f** (`8f26755f`) against **58b08c38** (`58b08c38`)

Run 2026-08-30T19:28:23+00:00 on ubuntu-s-2vcpu-8gb-160gb-intel-nyc1. Ladder `e9ef9250`. Scope `core`.

## The one line

stage moves 13, verdict moves 0, zig differs 44 of 1007

## What was run, and what was not

Emitted zig differed for **48** of 1233 programs. Only those were built and executed. The other 1185 emitted byte-identical zig on both arms, so with the same zig version they produce the same binary and cannot have moved -- not run, and not evidence of anything either.

## Population

base 1229, head 1233

**only_head** (4): gpu-devicemath-atan, match-shadowed-arm, real-bitcast-f64, real-int-conversions

## Stages

| stage | base | head |
|---|---|---|
| clean | 709 | 726 |
| codex-refused | 210 | 210 |
| markers | 298 | 285 |
| timeout | 4 | 4 |
| unresolved | 8 | 8 |

## Stage moves (13)

- `engine-animation` — base markers, head clean
- `hamt-test` — base markers, head clean
- `int-min-literal` — base markers, head clean
- `kvstore-test` — base markers, head clean
- `ota-gate-real` — base markers, head clean
- `pow-on-real` — base markers, head clean
- `rasterizer-test` — base markers, head clean
- `real-approx-equality` — base markers, head clean
- `real-literal-rounding` — base markers, head clean
- `real-neg-neg` — base markers, head clean
- `real-negate` — base markers, head clean
- `roc-fold-empty` — base markers, head clean
- `unit-real-arith` — base markers, head clean

## Verdict moves (0)

none

## Emitted zig differs (44)

- `builtin-alloc` — base_lines 1173, head_lines 1208
- `circbuf-test` — base_lines 434, head_lines 434
- `db-csv-roundtrip` — base_lines 1620, head_lines 1620
- `db-full-test` — base_lines 4000, head_lines 4000
- `db-row-update` — base_lines 1267, head_lines 1267
- `device-math` — base_lines 407, head_lines 428
- `engine-animation` — base_lines 927, head_lines 939
- `engine-culling-cost` — base_lines 1506, head_lines 1508
- `engine-mesh-gen` — base_lines 1671, head_lines 1673
- `engine-near-clip` — base_lines 1466, head_lines 1468
- `engine-render-heap` — base_lines 1498, head_lines 1500
- `engine-shading` — base_lines 1473, head_lines 1475
- `engine-shadow` — base_lines 1619, head_lines 1615
- `engine-software-render` — base_lines 1515, head_lines 1514
- `engine-texture-cost` — base_lines 1506, head_lines 1508
- `gop-scene-viewport` — base_lines 1550, head_lines 1551
- `hamt-test` — base_lines 622, head_lines 622
- `int-min-literal` — base_lines 333, head_lines 349
- `kvstore-test` — base_lines 644, head_lines 644
- `list-test` — base_lines 519, head_lines 519
- `matrix3-test` — base_lines 559, head_lines 579
- `ota-gate-real` — base_lines 572, head_lines 572
- `pow-on-real` — base_lines 312, head_lines 322
- `rasterizer-test` — base_lines 653, head_lines 668
- `raytracer-test` — base_lines 785, head_lines 799
- `real-approx-equality` — base_lines 342, head_lines 348
- `real-approx-modes` — base_lines 351, head_lines 357
- `real-bitcast` — base_lines 330, head_lines 346
- `real-literal-rounding` — base_lines 326, head_lines 336
- `real-neg-neg` — base_lines 334, head_lines 349
- `real-negate` — base_lines 364, head_lines 384
- `real-saturating` — base_lines 355, head_lines 371
- `real-saturating-finite` — base_lines 355, head_lines 377
- `real-trapping` — base_lines 355, head_lines 371
- `real-trapping-overflow` — base_lines 339, head_lines 355
- `roc-fold-empty` — base_lines 337, head_lines 337
- `roc-iter-drop-if` — base_lines 349, head_lines 347
- `roc-iter-keep-if` — base_lines 349, head_lines 347
- `roc-iter-map` — base_lines 349, head_lines 347
- `sparkplug-encode` — base_lines 893, head_lines 903
- `unit-real-arith` — base_lines 376, head_lines 374
- `vec-array` — base_lines 419, head_lines 429
- `vec-lanes-smoke` — base_lines 385, head_lines 395
- `vec-mask-hazards` — base_lines 413, head_lines 423
