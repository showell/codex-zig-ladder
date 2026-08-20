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
