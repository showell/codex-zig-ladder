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

## The gdbstub refill was Nagle-bound, and the rungs paid it (2026-08-24)

Six of the ladder's units bundle past the 1 MB ring, so `truth_arm`
refills for each of them -- twice, once per blob:

    passes_to_x86  2636469    1.59 MB over the ring
    ir_to_x86      2503544    1.46 MB over
    ir_to_wire     1158758     110 KB over
    lower          1114391      66 KB over
    ir_to_codex    1049870     1.3 KB over
    ir_to_codex_roundtrip 1049851  1.3 KB over
    check           974387    74 KB UNDER, the near miss to watch

Before `TCP_NODELAY` on the gdb socket, every 1 KB M packet cost 41 ms
-- a delayed ACK, not throughput, and the same 41 ms showed up on an
interrupt-plus-8-byte-read. Measured on `ir_to_x86-cdx.blob`, the whole
2503563-byte compile:

    fill 0.6s, stream 148s, SIZE 2150397     TOTAL 150.5s

The 1454987 bytes that crossed the ring are 1421 packets, so the old
path added 58.3 s of wall clock -- additive, because the guest is halted
for the entire write. 208.8 s before against 150.5 s after, 28% off one
rung compile, and about 258 s off a full pass over the units.

That lands on the REBANK, not the sweep: `truth_arm` is called by
`rebank_all.sh` and the `truthcycle_*` scripts, while `allcycles.sh`
runs `zig_arm`/`ring_arm` against truths already banked. Against a
rebank of roughly 1460 s (the 53-minute rebank+sweep of 2026-08-23 less
its 1716 s sweep, derived rather than timed) that is near a fifth.

The subject sizes come from bundling in the shared checkout, whose
generated harnesses may lag; the margins are wide except for `check`.

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

## The act-block tail arm does not move bare metal (2026-08-24)

`64d7db8e` ("tail loops: an act block is on the spine") puts `IrAct` on
the tail spine in all four ZigEmitter walks. The question a sweep can
answer about it is the narrow one -- does putting it there change what
the compiler emits -- and the answer is no.

Sandbox `20260824T193723Z-tailcall-sweep`, ladder `3e14078`, codex
`64d7db8e`, seed `a01c1547e92eb0d0` (Update 49). Natives built from
`64d7db8e`; phase 0b confirmed the same-day `ring_compile.py` change
compiles identical bytes, so the transport is not a variable here.

    rebank   12 units, 1637 s
    sweep    14/14 rungs green, 658 s
    census   CDX6020 x43, unmoved
    bare     14/14 byte-identical to truth/u49

The bare-metal row is the one worth keeping. The truths recorded in this
run came off the seed compiler with the emitter change in the tree, and
every one of them matches the bank taken before the change -- so the
emitter edit stayed on the emitter's side and did not reach the image.
`bank_truth.py` then took the bank from this sandbox and produced a
ZERO-BYTE diff against the committed `truth/u49`, which checks the same
claim through the provenance gate rather than through the sweep's own
comparison: all 14 sidecars matched the on-disk seed sha AND the
harness-content sha, so the files are not merely equal, they are equal
and were measured under the tree that is on disk.

What this does NOT establish, and the commit message says so first:
whether an act-bodied loop now FLATTENS. No stack number was taken
anywhere in the chain. 14/14 green is arm agreement against truths from
this same tree; it prices the change at "breaks nothing".

## The act arm fires, and every site it reaches is ours (2026-08-24)

Measured without new compute, which is why it is worth writing down.
`65cb244b` and `64d7db8e` differ in `ZigEmitter.codex` by exactly the
act arm's 74 insertions (`git diff --stat 65cb244b 64d7db8e --
codex/plugs/zig/ZigEmitter.codex`), and both sandboxes -- 
`20260824T132742Z-f37-parser` and `20260824T193723Z-tailcall-sweep` --
already hold a full set of emitted `ast/*.zig`. Counting the emitted
tail-loop form per subject is then a one-variable differential over
artifacts that already exist.

    subject                65cb244b  64d7db8e  delta
    lower                       519       525     +6
    check                       471       475     +4
    ir_to_x86                   893       897     +4
    parse                        58        62     +4
    passes_to_x86               992       996     +4
    desugar                     118       121     +3
    scope                       173       176     +3
    ir_to_wire                  537       538     +1
    lex                          10        11     +1
    codexir, ir_to_codex, ir_to_codex_roundtrip,
    lir_to_x86, zigemit                            0

The arm fires: +30 loops over 9 of 15 subjects. The parser change is
not manufacturing this -- it lives on the `65cb244b` side, and that
side gained no loop the act tree lacks in any subject, so every delta
above is positive in the act arm's direction only.

The result that matters is WHICH functions. All 18 distinct ones are
`show_*`, `print_*`, `fibx_*` or `whole_*`, and all of them are
generated by `ast/gen_*_harness.py` -- the ladder's own dump harness,
which turns a rung's output into truth text and ships nowhere. Not one
compiler function is in the list. `print-notices-loop`
(`opening.codex:1421`) is a genuine compiler act-loop of exactly the
shape the arm targets, and it appears in no emitted subject at all, so
this corpus cannot see the upstream benefit even where one exists.

So the branch's claim for `64d7db8e` is parity, not stack: the python
plug has always descended into an act's last statement and ours did
not. The two plugs disagreed about what a tail position is, and the arm
ends the disagreement. No stack saving for upstream is evidenced here,
and none should be claimed.
