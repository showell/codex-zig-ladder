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
