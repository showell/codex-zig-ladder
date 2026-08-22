# Justifications

Measurements behind decisions the rest of the repo states as plain rules.
One entry per decision, newest first. This file exists so the README and
the memory notes can say "do X" without re-arguing it; if a rule here ever
looks wrong, re-measure before overturning it.

## The bundle edits are image-preserving (2026-08-18)

`bundle_scope` strips `bsearch-text-pos`; `bundle_fibx` carries `CCE` and
`ListUtils` once each. Proof: `truth/u45` was banked before these edits and
`truth/u46` after, and all fourteen rungs are byte-identical across the two
banks -- the edits changed nothing either compiler emits.

## 2.5 GB address-space caps on emitted-binary runs (2026-08-19)

`corpus_run.py` and `zig_verdict` cap `zig run` at 2.5 GB RLIMIT_AS.
Measured basis: an emitted binary without the arena peaks past 3.0 GB
(fibx: 3,045,504 kB, OOM-killed) and twice livelocked the whole WSL VM
instead of dying (swap widens the livelock window; only a per-process cap
closes it). With the arena the same runs need ~240 MB, and a corpus
compile needs ~130 MB, so the cap only ever bites a runaway.

## The arena rides the pin branch (agreed Steve + Claude, 2026-08-19)

Update 47's emitter predates PR 71's arena; without it `fibx` and `whole`
cannot execute on this machine (measurement above), so the arena is
cherry-picked onto `u47-rebank`. This is the capacity carve-out in
"Processing a new Update" step 4: capacity prerequisites already landed or
filed upstream may ride the pin, correctness fixes may not.

## fibx and whole use the ring transport; the small rungs keep TCP (2026-08-16)

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

## Corpus run memory cap: 800 MB address space (2026-08-19)

After the second corpus-run livelock, the entire 299-program clean set was
replayed serially under `ulimit -v 819200` (800 MB RLIMIT_AS) with a 60s
timeout: zero cap hits, zero timeouts, max RSS 145 MB (`ttt-perfect`),
everything else at or under ~128 MB, max wall 4s. The only failures were
the five deterministic ~1s SIGABRT panics, which are recorded verdicts,
not hazards. `RUN_MEM_CAP` is therefore 800 MB -- the largest value the
corpus was actually measured under, not a guess from RSS (RLIMIT_AS caps
address space, and the compile stage's address-space use was not measured
separately). A runaway now dies by cap with ~3 GB of guest free, below
swap territory. Raise only on the evidence of a legitimate program hitting
the cap.

AMENDED 2026-08-20: raised to 2200 MB, on exactly that criterion. The
heap-unification emitter reserves 1.5 GiB of address space up front
(lazily faulted; resident unchanged at ~145 MB), so under it EVERY
legitimate program hits an 800 MB RLIMIT_AS cap at reservation. The
raise moves no banked verdict -- the 800 MB replay above had zero cap
hits, and the banked crashes are overflow panics -- so bank-vs-branch
movement stays attributable to the emitter. Balloon protection
survives (the balloon class was 3 GB+, and the new emitter's
region-exhaustion panic fires before a balloon can form). The
RSS-shaped guard (cgroup MemoryMax) is the queued long-term answer.
Headroom MEASURED 2026-08-20 (cold review's ask, not asserted): the
full shape -- 1.5 GiB reservation + the 512 MB spawn stack + zig
runtime, compile stage included -- ran green under RLIMIT_AS 2200.

Root cause of the livelocks themselves was never a corpus program: the
Windows C: drive at 98% left `swap.vhdx` unable to expand, so paging
stalled writeback and reclaim (forensics: claude-steve random887). Fixed
on the Windows side 2026-08-19; the cap is defense in depth.

## The host has been ~5x slow since 2026-08-19 14:53; measure it before blaming code

`ring_compile` prints a `stream:` line timing the seed compiling the zig-plug
bundle inside QEMU -- same workload, same code path, every sweep. It is a free
dynamometer for this box:

    12:30  413138 -> 410689 bytes   29s
    12:50            410689 bytes   29s
    13:30  399854 -> 411273 bytes   29s
    18:27  401344 -> 413138 bytes  149s
    19:20            413138 bytes  145s
    19:40            411273 bytes  146s

0.37% more input, 5.1x the wall clock, with `ring_compile.py` byte-identical
across the interval (`git diff 8a74c94..HEAD` touches only the READY wait and
the diags sidecar) and `-accel tcg` hardcoded, so this is not an accel flip.
`READY at` moved 0.3-0.4s -> 0.8-0.9s the same way. The intervening events are
the 14:53 WSL livelock, a Windows reboot, a large C: cleanup and a VHD sparse
conversion.

This matters because a 5x host makes healthy code look defective, and it did:
the `check` rung's 175s think time failed a 120s stall window and was
diagnosed as a transport ceiling and then as an emitter regression. 175 / 5 is
~35s, which is where it sat when it passed. **Read the `stream:` line before
attributing a slowdown to a commit.**

## Droplet compile venue: TCG beats KVM there, and the droplet beats the laptop (2026-08-20)

The droplet appliance (droplet_vm_setup.sh / droplet_compile.sh) was sized by
measurement before adoption. Same warmup plug blob (401353 bytes in, 377014
out), same ring_compile.py, guest at 1300 MB on the droplet:

    laptop  WSL2, tcg          stream: 31s    (the standing 29-31s contract)
    droplet DO-Premium-Intel,
            kvm                stream: 43s    READY at 0.4s
            tcg                stream: 26s    READY at 0.2s

KVM loses on this workload because the guest streams output through port
I/O and polls the serial LSR; every port access is a vmexit under KVM and a
cheap helper call under TCG. So the wrapper pins TCG. Byte-level acceptance:
the droplet CDX and .map are byte-identical to the laptop compile of the
same blob. Steal time zero during the runs; the 1300 MB guest fits the 2 GB
box without swap for this workload -- larger subjects (the 2.5 MB codexir
bundle) are unmeasured there and get their own measurement before any claim.

## Deck usage, both arms (2026-08-21)

Measured because the heap-unification branch died of a deck overrun and
"how much deck does bare metal actually use" was the question that decides
whether the fix is frugality or a bigger reservation.

Method: print the main frontier immediately before `x86-64-emit-cdx` --
which is exactly where `emit-build` places the deck -- and `__deck-pos`
after emission. Both reads happen OUTSIDE any extent, which matters:
BuildSettings records that the deck-pos cell is frozen at the deck's base
inside a phase-wide extent, so a probe taken inside one reads the base and
says nothing. Bare metal via `truthcycle_fibx.sh` on the u48 pin; zig arm
by patching the emitted `fibx.zig` prelude to track the high-water at each
outermost `__deck-exit`. `emit-build` reserves `defs*65536 + 25165824`.

    rung   defs  reservation   bare metal   zig arm     zig/bare  bare headroom
    fibx      3   25,362,432   23,654,536   33,977,960    1.437×    1,707,896 (6.7%)
    scale    61   29,163,520   23,708,712   34,027,664    1.435×    5,454,808 (18.7%)

Three things this says:

- **The zig arm needs about 1.44x the deck**, and the ratio is the same to
  three digits across a 3-definition and a 61-definition subject. That is a
  per-object representation cost, not a per-definition one: text is a
  16-byte slice here where bare metal carries a pointer, and every list is
  a CxList indirection plus an ArrayListUnmanaged header.
- **The `defs*65536` term barely matters.** Bare metal spends 23.65 MB on
  three definitions and 23.71 MB on sixty-one -- 54 KB apart. The 25165824
  constant is doing essentially all the work, on both arms.
- **Bare metal's own headroom on fibx is 6.7%.** The reservation is tight
  by design, so there is no slack for a fatter arm to grow into, and no
  amount of ordinary frugality closes a 44% gap. Worth raising upstream on
  its own: a 3-definition subject sits at 93.3% of its deck reservation,
  and the guard that should catch exhaustion cannot fire, because
  `deck-short-of` reads the frozen cell (BuildSettings' own note: starving
  the floor "did not raise CDX9002; it crashed in __text_compare on a
  garbage pointer").

Control, and the reason this is the whole remaining story: with the
reservation multiplied by four and **nothing else changed**, the branch
runs to completion and both rungs are byte-identical to the u48 bank
(fibx 282995 bytes, scale 336800). The heap unification is correct; it is
sized wrong.

Re-measured 2026-08-21 evening, after the day's branch fixes, on the swept
artifact itself: sandbox `20260821T204032Z-longsweep`, emitter `d3dc3536`,
`ast/fibx-slack.zig` = the swept `fibx.zig` with only `cx_deck_slack`
raised to 128 MB, peaks read from the CX-DECK instrument stream (stdout).
Bare-metal column unchanged from above -- same subjects, same seed.

    rung   defs  reservation   bare metal   zig arm     zig/bare  vs reservation
    fibx      3   25,362,432   23,654,536   27,014,528    1.142×   over by 1,652,096 (6.5%)
    scale    61   29,163,520   23,708,712   27,064,232    1.142×   fits, 2,099,288 free

The day's fixes cut the zig arm from 1.437× bare metal to 1.142×, again
flat across 3 and 61 definitions. scale now FITS its reservation; fibx
still overflows, but by 1.65 MB where the morning's gap was 8.6 MB. The
top-level placements used 103,127 and 1,392,861 bytes of their 109 MB.
With the slack and nothing else changed, both rungs run to completion
byte-identical to the u48 bank -- the correct-but-sized-wrong verdict
holds at `d3dc3536`.

The whole unit, same experiment (`ast/whole-slack.zig`, slack only): both
rungs run to completion byte-identical to the bank. Note carefully what
that does and does not say. The sweep's `Segmentation fault at address
0x9` is finding 24's signature exactly -- `st_append_code` reading
`st.workspace.code_capacity`, 0x9 = 1 + 8 against finding 24's 0x896 =
2190 + 8 -- so the honest reading is that MORE DECK SUPPRESSES FINDING
24's CRASH, which points at deck exhaustion as its cause rather than
clearing it as unrelated. PRIORITIES item 1 carries the follow-up.
Its emit placements, zig arm at `d3dc3536`:

    rung   defs  reservation   zig arm     vs reservation
    whole     5   25,493,504   27,016,144   over by 1,522,640 (6.0%)
    clamp    25   26,804,224   27,036,504   over by 232,280 (0.9%)

All four emit rungs now cluster at 27.0-27.1 MB across 3, 5, 25 and 61
definitions: the zig arm's flat cost is ~27 MB against the formula's
25,165,824 flat term. A ~2 MB bump to the flat term covers every measured
rung; the defs term can stay.

## The finding 24 slack experiment (2026-08-21 evening)

The bump above covers the EMIT rungs and only them. The same
slack-one-constant methodology on finding 24's own reproducer -- census
natives at `1db8a78c`, `codexir` fed the 2,496,998-byte fibx subject on
stdin -- says the codexir workload is a different animal:

    slack      wall     outcome                                     deck used at death
    0          17.6s    GP fault, finding 24's exact frames         191,933,132
    256 MB     103s     cx heap: exhausted at 1610611665 + 1725     381,012,596+

Slack removes the corruption entirely (the GP fault never happens, the
run gets 40x more IR out) and the program then exhausts the full
1,610,612,736-byte arena legitimately. Deck use is monotonic in the
instrument stream, no rewind ever, and scales past whatever room it is
given, against a demand-lift-floor of 109,051,904 that both arms compute
from the same source. Bare metal compiles this subject inside its arena.
Conclusion recorded in finding 24: corruption = deck overrun trampling
(closed); the open defect is deck-allocation VOLUME on this arm, not
reservation sizing, and no flat-term bump fixes it.
