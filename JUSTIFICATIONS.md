# Justifications

Measurements behind decisions the rest of the repo states as plain rules.
One entry per decision, newest first. This file exists so the README and
the memory notes can say "do X" without re-arguing it; if a rule here ever
looks wrong, re-measure before overturning it.

## Update 52 before the rungs: the arms that answer for the compiler alone (2026-08-28)

Update 52 has to be judged on its own, and the obstacle is that TWO emitter
deltas now sit between it and the u51 bank. PR 93's absorb (`3942e362`) moved
`ZigEmitter.codex` by 202 lines and added `ZigStdio.codex`; PR 95 is open on
top of that. The register said "U52 touches `codex/plugs/zig/` not at all --
0 lines", and that is true only from `3942e362`. **Our bank is at `012a9d2e`,
and from there the emitter has moved.** So a zig-arm diff u51->u52 carries two
variables and a bare-metal one carries none.

These are the measurements taken BEFORE any plug ran, each answering for the
compiler by itself.

**The host contracts did not move.** `ram-size-addr = 4072` (0xFE8) and
`serial-ring-buf-size = 1048576` are identical at both pins, and
`X86_64Boot.codex` -- what `ring_compile.py`'s cells 28704/28712 are pinned to
-- is unchanged. `tools/codex-vm.c` did move 20 lines, which is the file the
ceremony flags, but the change makes an unrecognised flag exit 2 instead of
being ignored, in a Windows tool we never invoke. No contract our side
hard-codes was touched.

**The seed probe: byte-identical.** One subject (`plug-oracle-arith`), one
host, one blob, only the seed varying:

    u51  seed C3181693 -> 110,758 bytes  sha 759e0760baad38fc
    u52  seed 61C81B04 -> 110,758 bytes  sha 759e0760baad38fc   4.9s each

Weak evidence on its own -- one small subject, and it barely exercises the 266
lines Update 52 moved in `X86_64.codex` -- but it is what the ceremony asks
for: the new seed boots under our QEMU flags, takes the ring preload, and
emits an image our reader parses.

**The tier gold: 21 of 21 columns byte-identical.** `./tiers_run.py --bare`,
SET GREEN, banked to `findings/gold/u52/`. `gold_key` is
sha256(program text + seed), so all 21 keys moved on the re-pin and every file
differs; with the key line excluded, every column is byte-identical to u51's.
Arithmetic, buffers, CCE, chars, closures, composites, decks, identity, list
mutation, lists, records, tail calls, text, text semantics, the memory model,
fresh spans, peek-qword, record layout, char ops, char literals, approx-eq.

This is the arm that cannot be muddied, and `gold_key`'s own docstring says
why: "the plug is not in that list -- bare metal is the oracle precisely
because no plug is in its path -- so a banked column stays valid across every
emitter change." Twenty-one bare-metal columns agreeing across a seed re-pin
is the strongest statement about Update 52 alone that is available before the
rungs run.

**What this does NOT say.** Nothing here has exercised the plug, and a green
zig sweep afterwards is a self-contained U52 claim (plug-under-U52 against
bare-metal-under-U52) that needs no attribution. Only a RED needs the split,
and the split is available: the u51 emitter is one `git show` away and can be
dropped into a second sandbox to A/B the rung that failed.

## Compiler-only sweep, 2026-08-27 21:52Z -- 14/14 green, and superseded on arrival

Tree `53979eeb`: the u51 pin plus COMPILER-30 and findings 57, 58, 59.
**Zero ZigEmitter commits**, which is the point -- `README.md` says sweep the
release's emitter verbatim, and every earlier sweep this evening had our four
plug fixes in the tree, so each measured a compiler nobody ships.

    natives                 5m46s
    corpus --transpile      606 programs: clean 328, markers 249, unresolved 16,
                            codex-refused 13     (population 53979eeb, clean)
    corpus --run            328 built and run: match 275, refused 27,
                            no-expected 23, hardware-only 2, crashed 1
    sweep                   14/14 rungs green, 1780s

**No program regressed.** All 23 verdict moves accounted for: 7 markers->match,
3 markers->refused (newly BUILT and failing, two on our own finding-61 gap which
is deliberately not in this tree), 12 zigemit->codex-refused which is our own
error-gate relabelling.

**Two caveats the sweep prints about itself, and they are not small.**

    IR REBUILT ... bare metal was NOT re-measured in this sweep
    TRUTHS RESTORED FROM THE BANK -- this sweep says the plug still reproduces
    the bank, NOT that bare metal was re-measured
    CENSUS NOT COMPARED: ... ensure_ir.sh rebuilt the IR, so no bare-metal
    .diags exists for those units

So it covers the rungs and not the diagnostics, and its bare-metal side is the
u51 bank rather than a fresh measurement. `desugar`, `check` and `lower` are
themselves rung subjects and this tree changes all three, which is what makes
the byte-identical result meaningful rather than trivial.

**SUPERSEDED ON ARRIVAL.** The mirror push landed at 20:26Z, mid-sweep: the pin
is now `3942e362` with seed `4341370C`, and Damian asked for the second PR to be
measured against it. This result is a true statement about a base nobody ships.
It is kept because it is evidence the three compiler fixes are
semantics-preserving on the rungs, and because the re-measure at the new pin
will want something to compare against.

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

## The curried-apply fix does not move bare metal either (2026-08-24)

Finding 40's fix is two sites in `ZigEmitter.codex` and nothing else, so
the question a sweep answers about it is the narrow one: does correcting
how an over-applied definition is CALLED change what the compiler emits
anywhere else. It does not.

Sandbox `20260824T220516Z-f40-fix2`, ladder `91020ad`, codex `835639b7`
(off PR 77's `8cb8a0e4`), seed `a01c1547e92eb0d0`.

    tiers    22 tiers, SET GREEN (prim-closure rejoined)
    rebank   12 units, 1637 s
    sweep    14/14 rungs green, 657 s
    census   CDX6020 x43, unmoved
    bare     14/14 byte-identical to truth/u49

The bare-metal row is the one that prices the change. The truths in this
run came off the seed compiler with the fix in the tree, and every one
matches the bank taken before it; `bank_truth.py` then produced a
zero-byte diff, which checks the same claim through the provenance gate
rather than through the sweep's own comparison.

The tier that motivated the fix now reads as designed: `control-flat` and
`control-pick` agree across the arms, `under-mutual` answers 47 here and
`not-47` on bare metal, and that single row is admitted in
`gold/EXPECTED.txt` as COMPILER-18. It is the detector arming, not a
workaround -- the day bare metal keeps the arity the arms agree and the
mark turns `??`.

Cost note for the ERGONOMICS queue: of the ~38 minutes this took, 27 were
the rebank, and the rebank was needed only to produce `.ir` files. The
seed did not change and bare metal was never in question. That is the
measurement behind `ast/ensure_ir.sh`.

## A fresh sandbox can sweep, and it costs 1499 s (2026-08-24)

The claim being tested is that a sweep does not need a rebank behind it.
Sandbox `20260824T225947Z-ensure-ir-test`, cut from nothing: no natives, no
`.ir`, no `.truth`, no generated harness.

    full rebank + sweep   2294 s   (1637 s rebank + 657 s sweep, same 12 units)
    restore + ensure_ir + sweep   1499 s

**13 minutes back, against the 27 that was estimated.** The estimate
assumed `ensure_ir.sh` skipped most of the truth arm; it skips the cheaper
half. What it drops is the bare-metal binary compile and the subject run.
What it still pays, per unit, is the bundle and the IR-CCE compile through
the ring -- and the ring compile is where the time is, which the Nagle
entry above already measured at 148 s of stream for `ir_to_x86` alone.

The percentage is the smaller result. The larger one is that a fresh
sandbox can sweep at all: before this it could not, and the only way to
make the files it was missing was to re-measure an answer already banked.
Three things were missing, and the list was arrived at by running rather
than by reasoning -- the generated harness (found when pwsh was handed a
`LexHarness.codex` that was never there), the `.ir`, and the truths.

What this run does NOT establish: that `allcycles.sh`'s integrated restore
works from empty. The truths were already on disk from a manual
`restore_truths.py`, so the sweep took the "keeping" branch. The restore
tool is proven -- 14 truths and sidecars, all passing `check_rung`, no
harness drift -- but the wiring has not fired in anger.

The sweep says so itself, which is the point of the two lines it now
prints: `IR REBUILT for <units> -- bare metal was NOT re-measured in this
sweep`, and a census that declines to compare rather than judging half a
population against a whole-population pin.

## A prose block moves the plug and not its output (2026-08-25)

The zig plug's stack note is compiled source, not a comment in a host
language, so "it is only prose" is an argument rather than a measurement.
Steve gated the outbound prose PR on the measurement.

Branch `zig-plug-stack-prose` at `87f55675` against the seed-6cf4a8e0
sweep, both on the same pin (`0c4327d5`), sandbox
`20260825T142003Z-prose-verify`:

    bundle        10072 lines, 484804 bytes  ->  10094 lines, 486098 bytes
    fingerprint   1aba3c41196cb74e           ->  73dc2f1e8cd0ed81
    sweep         14/14 rungs green, 1627 s
    emitted zig   13 files, every one byte-identical

A different plug binary, by 22 lines and 1294 bytes, emitting the same
program for all thirteen subjects. That is the whole claim: the prose is
carried through the bundle and the fingerprint and reaches nothing the
emitter writes.

The comparison counted what it compared -- thirteen files against thirteen
files -- because a glob that matches nothing produces the same happy
verdict as a glob that matches everything, and this one is run once and
believed.

## The deck costs ~145 MB per MB of source near the ceiling, and it is all the front end (2026-08-25)

Measured by `./codexzig_scale.py` across every `ast/*-subject.codex`,
reading the `CX-DECK used=` trace the emitted runtime prints on stdout.
**That script is the runner behind this table and behind finding 45** -- it
re-measures the row, then squeezes the reservation and checks the failure is
still the one the finding describes. Neither number is one that was true
once. The deck
reservation is 512 MB (`reserved=536870912`).

    subject                  source   deck peak  headroom   vs duo
    lex                      0.12 MB      7 MB      99%      same
    parse                    0.42 MB     68 MB      87%      same
    desugar                  0.44 MB     80 MB      85%      same
    lir_to_x86               0.48 MB     43 MB      92%      same
    scope                    0.53 MB     89 MB      83%      same
    check                    0.97 MB    144 MB      73%      same
    ir_to_codex              1.05 MB    180 MB      67%      same
    ir_to_codex_roundtrip    1.05 MB    180 MB      67%      same
    lower                    1.11 MB    171 MB      68%      same
    ir_to_wire               1.16 MB    179 MB      67%      same
    ir_to_x86                2.50 MB    356 MB      34%      same
    codexir                  2.62 MB    384 MB      29%      same
    passes_to_x86            2.64 MB    385 MB      28%      same
    codexzig                 2.87 MB    421 MB      21%      same   <- its own bundle

All fourteen emit zig byte-identical to `codexir | zigemit`, which is the
breadth half of the same run; the deck column is what it was for.

**The ratio is not constant and the average is the wrong summary.** The
per-subject ratios run from 89.6 (lir_to_x86) to 181.8 (desugar) -- a 2x
spread, with the SMALL subjects taking the HIGHER ratios, which is the
opposite of fixed overhead. `codexzig_scale.py` averages the subjects over
300 KB and gets ~153 MB/MB, hence a ceiling near 3.4 MB. But the four
subjects above 2 MB -- the only ones anywhere near the reservation -- average
**145 MB/MB**, giving **3.5 MB**, and the model's own largest point
contradicts it: at 2.87 MB it predicts 439 MB where the measurement is 421.

So quote **~145 MB/MB and a ceiling near 3.5 MB** for anything about the
ceiling, and treat 153 as what it is: an average over a range whose small
end will never be near the limit. An earlier revision of this entry replaced
145 with 153 on the grounds that the runner recomputes it. Recomputability
is not accuracy, and that was the wrong trade. The compiler's own bundles
are 2.5-2.9 MB today and every Update adds chapters.

**The whole cost is the FRONT END, and combining the halves is free.** On
`codexir-subject.codex` (2.62 MB), run three ways:

    codexir alone (front half)   384 MB
    zigemit alone (back half)      -    NOT INSTRUMENTED, see below
    codexzig (both, one arena)   384 MB

**The zigemit row is not a measurement and must not be read as one.** A cold
read caught this: `ast/ZigEmitHosted.codex` carries no deck prologue -- no
`init-phase-allocator`, no `__heap-save`, no `__deck-set`, no
`__heap-advance` -- so in the emitted `ast/zigemit.zig` the deck base and top
stay zero and `cx_deck_report` returns at its first guard on every call.
**zigemit cannot print a CX-DECK line however much memory it uses.** The
tracer's absence was reported as a measured zero.

What the OTHER two rows do establish is the load-bearing part and it stands:
codexir alone and codexzig on the same subject both peak at 384 MB, so
carrying the emitter in the same process adds nothing measurable to the
deck. `codexzig`'s headroom is `codexir`'s and the two-heap worry that was raised against combining the
halves does not apply to this region at all. It also means the ceiling is not a property of
the combined program: `codexir` in the two-process pipeline hits it at the
same input size, and the ladder would meet it first through whichever rung
bundles the most chapters.

**"Runs out" is shorthand and finding 45 is the literal truth.** Crossing
the reservation does not stop anything: the tracer prints negative headroom
and the program keeps allocating to roughly twice the reservation before it
faults. So the ceiling is where behaviour becomes undefined, not where a
refusal happens -- which is the point of finding 45 and the reason to fix it
before the compiler grows into it.

This is the deck (the phase allocator's region), NOT the 512 MB thread
stack `stack_probe.py` measures for finding 37. Two constants that happen to
share a number.

**And the reservation is not enforced -- finding 45.** Rebuilding codexzig
with the literal lowered (ten seconds, no VM) and feeding it a subject that
wants more: the tracer prints negative headroom for fifteen more steps, the
program reaches 200% of the reservation, and then takes a General protection
exception inside `cx_list_at`. No partial zig is written, so the failure
cannot be mistaken for success -- but nothing names the deck, either.

## Thirty percent of the "emitter gaps" are not gaps (2026-08-26)

`corpus/gaps.json` is the histogram that RANKS which emitter arm to write
next. Banked 2026-08-26 over 596 programs, split by what the marker
actually says:

    no emitter for              91 distinct /  947 program-hits
    unresolved type variable    40 distinct /   51 program-hits
    other                        4 distinct /   15 program-hits
    TOTAL                      135 distinct

**Only the first row is an emitter gap** -- a builtin with no rule, which
is a named piece of work. The second is the finding-46/47 class: a type
argument the emitter could not resolve. That is a DEFECT, and two of them
are already filed, so it is not work the histogram should be ranking.

**And the distinct count flatters that row badly, because those markers are
keyed by FUNCTION NAME.** `unresolved type variable T88 of hamt-fold` and
`T16 of __lam_1` are separate entries, so forty distinct entries cover
fifty-one program-hits -- roughly one apiece. A single real gap,
`no emitter for poke-32`, reaches 123 programs by itself.

**So "distinct gaps" is the wrong number and this file has been quoting
it.** The 135 -> 133 -> 135 movements tracked across 2026-08-26 are mostly
that keying: the last two came from ONE ported program hitting finding 47
in two lifted lambdas. **Program-hits is the number that ranks work**;
distinct-count is a rename away from moving on its own.

Measured with the banked `corpus/gaps.json` by prefix, no re-run needed.
The cheap improvement, if anyone wants it: bucket the tvar markers under
one key and keep the function names as detail.

## A seed compile costs ~15 KB of SOURCE per second, and nothing else (2026-09-02)

Four seed compiles, two of them minutes apart in one native build, one of
them from the entry above:

    subject      source       output       wall    source rate
    ringplug     380,646     521,681      25 s     15.2 KB/s
    zigemit      380,323   1,201,081      25 s     15.2 KB/s
    codexir    2,737,563   9,369,123     178 s     15.4 KB/s
    ir_to_x86  2,503,563   2,150,397     150 s     16.6 KB/s

**`ringplug` and `zigemit` are the pair that settles it.** Same source size
to within 300 bytes, 2.3x the output, identical wall clock. The cost is what
the seed READS, not what it writes and not what it computes.

Input is free and stopped being interesting when the refill went NODELAY:
`codexir`'s 9,369,133-byte IR crossed into the guest in 2.4 s, 3.9 MB/s.

**This corrects how the gdbstub entry above reads.** `stream: N bytes in Ns`
starts its clock at `t1`, which `ring_compile.py` sets immediately after
`gdb.detach()` -- before the guest has compiled anything. The guest prints as
it goes, so that line is elapsed-to-last-byte over the whole compile, not a
transport measurement. `fill 0.6s, stream 148s` is not 148 seconds of
serial; it is a 2.5 MB compile that took 150 s, which is this rate. The
Nagle finding itself stands -- it was measured on the gdbstub WRITE path and
the 58.3 s it removed was real -- but nothing in this tree has ever shown
output transport to be the bound.

**The lever this leaves is bundle size, and only bundle size.** A rung costs
what its bundle weighs: the U54 truths run lex 15s, parse 46s, desugar 57s,
scope 70s, check 118s, lower 152s for no reason except that each one carries
more of the compiler than the last. The ring plug rebuilds in 25 s because
it is a 7,342-line slice -- the emitter plus the ring transport -- against
`codexir`'s 57,980 lines. Estimating before you launch is division.

A plug run is NOT this rate and must not be estimated with it: the same
build's `zigemit` transpile pushed 1,201,091 bytes in and got 539,566 out in
9 s. That is a different program on the guest, and it has its own curve.

Measured in sandbox `20260902T195222Z-u54-plug6` from artifact mtimes and
the transport logs; the `ir_to_x86` row is the 2026-08-24 entry's own.
