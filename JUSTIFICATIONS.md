# Justifications

Measurements behind decisions the rest of the repo states as plain rules.
One entry per decision, newest first. This file exists so the README and
the memory notes can say "do X" without re-arguing it; if a rule here ever
looks wrong, re-measure before overturning it.

## The bundle edits are image-preserving (2026-08-18)

`bundle_scope` strips `bsearch-text-pos`; `bundle_ir_to_x86` carries `CCE` and
`ListUtils` once each. Proof: `truth/u45` was banked before these edits and
`truth/u46` after, and all fourteen rungs are byte-identical across the two
banks -- the edits changed nothing either compiler emits.

## ir_to_x86 and passes_to_x86 use the ring transport; the small rungs keep TCP (2026-08-16)

The TCP receive path costs ~130 bytes of guest heap per IR byte (measured
per-stage: frame sim 45, bytes-to-text 34.5, byte-list build 11, buf-read
8, plus parser 35), so a 13 MB IR exhausts a 3 GB guest. `read-serial-cce`
costs 1 byte per byte. The TCP arm stays for the rungs that fit because it
exercises the Codex network stack on every sweep -- it is the surface that
caught the odd-frame DMA defect.

## TCP transfer acceptance: parity proof first, two-chunk agreement as fallback

`plug_run_checked.py` accepts a transfer when the pcap parity proof holds
(frame parity follows TCP payload parity, `pcap_parity.py`); when the proof
cannot be established it falls back to requiring two transfers at DIFFERENT
chunk sizes to agree. Different sizes because identical-size reruns
reproduced the identical corrupted byte 10 times in a row -- same-size
agreement proves nothing. Full record: `findings/PLUG_IR_TRANSPORT.md`.

## Droplet compile venue: TCG beats KVM (2026-08-20)

Same warmup plug blob (401353 bytes in, 377014 out), same `ring_compile.py`:

    kvm    stream: 43s    READY at 0.4s
    tcg    stream: 26s    READY at 0.2s

KVM loses on this workload because the guest streams output through port
I/O and polls the serial LSR; every port access is a vmexit under KVM and a
cheap helper call under TCG. So `~/.codex_ladder_env` pins TCG. The guest
is pinned at 3072 MB there because the seed guest dies silently pre-READY
above it (measured 2026-08-22: 3072 ok, 3584 dead).

## Deck usage, both arms (2026-08-21)

Measured because the heap-unification branch died of a deck overrun and
"how much deck does bare metal actually use" decides whether the fix is
frugality or a bigger reservation. Method: print the main frontier
immediately before `x86-64-emit-cdx` -- where `emit-build` places the deck
-- and `__deck-pos` after emission, both OUTSIDE any extent (inside one the
deck-pos cell is frozen at the base and a probe reads nothing). Bare metal
via `truthcycle_ir_to_x86_on_fib.sh`; zig arm by tracking the high-water at each
outermost `__deck-exit`. `emit-build` reserved `defs*65536 + 25165824`.

    rung              defs  reservation   bare metal   zig arm     zig/bare  vs reservation
    ir_to_x86_on_fib     3   25,362,432   23,654,536   27,014,528    1.142x   over by 1,652,096 (6.5%)
    ir_to_x86_on_cce    61   29,163,520   23,708,712   27,064,232    1.142x   fits, 2,099,288 free

The ratio is flat across 3 and 61 definitions: a per-object representation
cost (16-byte text slices, CxList indirection), not a per-definition one.
The `defs*65536` term barely matters -- bare metal spends 54 KB more on 61
definitions than on 3; the flat term does all the work, and bare metal's
own headroom on the fib subject is 6.7%. All four emit rungs (the `_on_`
four) cluster at 27.0-27.1 MB on the zig arm. Control: with the
reservation raised and nothing else changed, every rung runs to completion
byte-identical to the bank -- the heap unification is correct, it was
sized wrong.

**Landed as 4 MiB, verified 2026-08-22** (branch `5c9948f6`, sandbox
`20260822T021230Z-item2-flatterm`, fresh ring plug, fresh seed-compiled
subjects, `cx_deck_slack` 0): `X86_64Chapter.codex` now reserves
`defs*65536 + 29360128`. The bare-metal truths for the four emit rungs
re-ran on the bumped source and are byte-identical to `truth/u48` -- the
reservation never reaches the output -- and the zig arm passes all four
(`_on_cce` headroom 6,747,128; `_on_arith` 4,387,816). 4 MiB rather than the ~2 MB
minimum because bare metal's own margin is 6.7% and 2 MB would have left
the zig arm 1.6%.

## The deck census (2026-08-22)

`deck_census.py` on the census natives (`1db8a78c` tree), the ir_to_x86 subject
`8067da49…` (2,496,998 bytes), sandbox `20260822T014639Z-f24-volume`. Every
deck byte keyed by (allocator call site, outermost deck-record bracket);
main-heap bytes by call site. Three runs, IR byte-identical each time.

    arena     slack    wall    outcome                       deck at end   main at end
    1.5 GiB   256 MB   78s     exhausted (main+deck > arena) 381,663,332   1,226,834,574
    2.5 GiB   512 MB   63s     rc 0, 13,193,485 bytes of IR  ~381 MB       ~1.1 GB

Deck by bracket site (top six of 176; the full table prints from
`deck_census.py report`):

    parameterize_walk_sum_ctors      49,801,752   2,075,073 allocs   24 B avg
    desugar_def                      48,363,576   1,496,826          32
    lower_chapter                    38,726,096     974,434          39
    parameterize_walk_children       37,699,904   1,178,122          32
    make_end_node                    36,917,144   1,258,539          29
    make_token                       30,302,596     473,478          64

Deck by allocator call site: `cx_new` instances take 14 of the top 15 rows
at 16-64 bytes each (records, bare metal's fields*8); `cx_ll_empty` is 24
bytes per call against bare metal's 16 and accounts for ~33 MB of the deck
and ~190 MB of main; ArrayList growth is under 20 MB of deck in total.
Nothing is superlinear; nothing is 150x. Against the real driver's
per-phase floors (BuildSettings: check 648 MB, lower 328, parse 384+392,
resolve 200, lift 104, scope 104, lex 96, desugar 72) every phase's share
is a fraction of its floor. The harness's 104 MB was the LIFT floor
standing in for all of them.

Main heap by call site, top rows: `cx_ll_empty` 122 MB (5.1M calls),
`cx_new` 24-byte records 122 MB (5.1M), `cx_new` 64-byte 118 MB, i64
ArrayList growth 109 MB, SkipNodeText ArrayList growth 109 MB. Spread, not
a spike.

Downstream of the completed IR (findings 33, 34): `native/zigemit` needs a
>2 GiB thread stack to tokenize 3,282,147 tokens without tail calls, and
then exhausts its 1.5 GiB arena at 1.23 MB of output with no per-def
reclaim. The seed's `ir_to_x86.ir`, decoded, differed from the native IR in
930 of 3,822 lines for three causes: def order, chapter name, and `ctd`
vs `record-ty` for let-binding types. The last was the harness running
RESOLVE where `compile-frontend-ir` never does (ladder `3192fe5`); with
that gone (re-measured 2026-08-23, natives from heap `8cb8a0e4`, codexir
under MemoryMax=6G in 33 s) the diff is ONE line of 3,825: the chapter
name, `"Program"` on the seed's arm against `"Parsmi--FibxHarness"` on
the native one. Def order matched too -- it was RESOLVE's reordering.

## The resident bound, measured (2026-08-23)

Every emitted-binary and corpus run is bounded by cgroup MemoryMax
(`bounded_run`, `720d115`), not RLIMIT_AS. The address-space caps that
stood from 2026-08-19 counted the emitter's up-front reservation, so the
arena could never grow past the cap even though a reservation costs
nothing resident; a runaway now dies oom-killed under the cgroup, which
the corpus records as its own verdict. Verified end to end on the droplet
in sandbox arena-4g (natives from heap branch `6bf05013`, region
4 GiB): tiers SET GREEN, census moved no verdict, sweep 14/14, bank
retaken with only the known step-5 lex rename moving (`3c72b3f`).

The measurement the change exists for: `native/codexir` on the ir_to_x86
subject under `systemd-run --user --scope -p MemoryMax=6G` completes
rc 0 in 34 s (droplet, 2 vCPU; finding 24's run was 63 s laptop-side),
IR 13,223,342 bytes, byte-identical across two runs. Peak resident
2,469,888,000 bytes (2.30 GiB) against the 4 GiB reservation -- the
reservation is lazily faulted exactly as claimed, and the same subject
was IMPOSSIBLE under the old 2560 MB address-space cap, which the
reservation alone exceeded.
