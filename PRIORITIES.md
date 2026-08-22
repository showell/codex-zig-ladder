# What is next, in order

Kept here rather than in anybody's head or memory file, because there are now
several threads and they were drifting apart. If a memory or an essay disagrees
with this file, this file wins. The README's "Processing a new Update" is
the ceremony's step list; this file adds items and says where they slot --
on a conflict about ORDER, the README's list is the spine. Dated entries so staleness is visible. Done
items leave the list -- git history is their record, DONE.md holds one line
and a pointer each when a pointer helps, and measurements go to
JUSTIFICATIONS.md. This file is the queue, not the diary.

Every numbered item opens with an **Objective** line saying what the work is
trying to achieve, and in which of three modes it runs -- because the same
40-minute run means different things in different modes, and mistaking one
for the other misprices the work:

- **Hunting.** Fishing for defects that are not ours -- the project's actual
  product. A surprise is the payoff; a clean pass is a mild disappointment.
- **Due diligence.** Verifying that our own changes break nothing. On the
  happy path this is pure wall time: launch it, let it run, read one line.
  Only a red result is information, and green earns no celebration.
- **Instrument work.** Making the harness itself honest or cheap. It neither
  hunts nor verifies, but the other two modes are only as trustworthy as it
  is.

## The native loop, which changes what is cheap

Built by `native_build.sh`:

    native/codexir   .codex -> IR      ~0.1s
    native/zigemit   IR     -> .zig    ~0.05s

No QEMU in either. A Codex source to a running zig program is about a third of
a second. Rebuild both after any emitter change; that script is also the only
thing that compiles the plug **through itself**, which is how the
`comptime_int` defect surfaced.

The ladder is still the ladder: expensive, per-Update, and it answers "does the
whole compiler survive transpilation". Everything below is the cheap loop.

---

## 1. The heap unification -- the branch carries the fixes, one crash open

**Objective: land our own fix; finishing it is hunting our own plug.**
`findings/zig-heap-unification.md` for the design and the deck diagnosis;
`findings/README.md` 21-29 for what the unit tests found. Read the
EXCLUSIONS before touching anything -- several plausible mechanisms are
recorded as refuted, each with the test that killed it, and re-running them
is the main way to waste a day here.

Landed on `zig-plug-heap-unification` 2026-08-21, each measured on both
arms. **The branch was reworded 2026-08-21 evening** -- every commit now
carries a Confidence paragraph naming what verifies it and what does not;
trees are byte-identical, only hashes moved (this file and the findings
were swept to the new ones; sandbox MANIFESTs keep the hashes they built
at). `git log --oneline master..zig-plug-heap-unification` is the list;
what each one bought:

    17329ed9  __list-with-capacity honoured, and a cursor-collision refusal
    e4d2fcd1  a deck allocation overrunning its reservation now refuses
    8d9dbbe7  list constructors reserve the true total -- 6.96 MB of deck
    0e24f7cf  text concat extends in place            finding 22, asymptotic
    a9a329a0  an uncovered codepoint substitutes      finding 23
    3a490b8c  peek-qword wraps                        finding 26
    c7feba61  reserve with rawAlloc                   finding 27
    54242279  substring traps out of range            finding 28
    e4aa698d  substring and split copy                finding 29
    b4651d81  text-replace copies                     finding 29, 4th site
    2a1177fa  shift counts masked to six bits         finding 30
    b85f1b98  address-of returns an identity           finding 31
    9e929383  the deck high-water instrument
    4e118db1  instrument v2, corrected by its own run
    4101e62f  instrument v3, corrected by a review

Finding 23 is the one that unblocked the native loop on real source, and
finding 27 took a compile from 38.0s real / 15.3s sys to 11.4s / 1.8s,
because the old code committed all 1.5 GiB.

Natives rebuilt 2026-08-21 EVENING in sandbox `20260821T215618Z-natives-census`
at `1db8a78c` (branch tip), so they now carry every fix through
`2a1177fa`/`b85f1b98`. **`2a1177fa` is CONFIRMED against bare metal**:
`./tier_run.py findings/probe-shift-count.codex` is 17 lines byte-identical
to `findings/gold/probe-shift-count.txt`. `prim-text` through the same
natives agrees on every semantic row (`replace works yes` both arms, which
is `b4651d81`); its 12 differing rows are all COST rows, and the zig column
is now mostly BELOW bare metal where it used to be above.

That rebuild also surfaced a harness defect worth knowing about: the marker
scan counted the prelude's `cx_address_of` comptime guard as a refusal, so
**every native build had been refusing itself since `b85f1b98` landed** --
one marker in 2.7 MB, from prelude text no subject reaches. Same guard
printed a spurious `gap:` on every `tier_run`. Both now read
`findings/prelude-comptime-guards.txt`; read that file before adding to it.

**The full census ran on those natives 2026-08-21 (resumed and finished
that evening; sandbox `census_full_resume2.log`) and is the branch's
corpus due diligence: 323 clean programs, match 172 / refused 111 /
no-expected 30 / differ 5 / crashed 3, and vs the 08-20 bank 33 verdicts
moved -- every one an ex-codexir abort the heap fixes unblocked (10 to
match, 13 to markers, 6 to refused, 3 to differ, 1 to no-expected).
Nothing that was green regressed.** Every red was then chased to a cause,
and all of them are the unabsorbed PR 76: the three differs
(stringbuilder-test and stats-wrap-test print `?` for newline --
`cx_char_to_text` double-encoding a CCE 1 through `cx_cp_to_cce`, the
codepoint-Char model; validation-rules fails accented/Cyrillic
is-letter) are the char-CCE migration `ea8d51ac`; the carried
text-fold-indexed differ is named in that commit's own message; and the
three integer-overflow crashes (bloom-spread, consistent-hash-balance,
particle-spread) are named in `78e8da1b`'s message as fixed. The census
canary's expect-match four all held. When PR 76 absorbs, all eight reds
should flip -- if any survives absorption, THAT is a new finding.

**The natives must be rebuilt after any emitter change, and that is the gate
for everything downstream.** `native_build.sh` in a sandbox, >25 minutes, and
nothing else may touch the CPU while it runs: the guest asks for 3072 MB on
a 3849 MB box, and a concurrent `zig run` is enough to stall its transport
mid-transfer. **It runs HERE, not on the droplet** -- that venue pins a
1300 MB guest and the build does not fail there, it HANGS (three seconds of
CPU in eighteen minutes, no output). `native_build.sh` refuses the droplet
venue outright now; the toggle remains right for the sweep's ordinary rungs.

**The sweep re-ran locally 2026-08-21 and answered: 10/12 green, both emit
rungs still red -- but red LOUDLY now.** Sandbox
`20260821T204032Z-longsweep` (ladder `5a881b0`, codex `d3dc3536`, fresh
`.ir` for all twelve units under seed 930ff7f1, handed in by hand -- the
droplet attempt earlier that day died at launch on missing gitignored
`.ir`). The ten non-emit units are byte-identical against the banked
truths. The two emit units:

    fibx   panic: cx heap: the two cursors met -- alloc at 141181824 + 24
           crosses (hp=141181824 dptr=115819408 bivy=141181840 nest=1)
    whole  Segmentation fault at address 0x9

Transport was clean for both (rings refilled fully, CCE sizes matched), so
both failures are in the running program. Neither zigraw carries a single
CX-DECK line. The sandbox ladder predates the sweep-digest commit
(`00cf4bd`), so these artifacts under `ladder/ast/` are the only record --
the console verdict died with a WSL crash at ~21:37Z. What this buys:

- The Text-narrowing question is answered by the slack re-run (evening,
  JUSTIFICATIONS deck table, second column): the fixes cut the zig arm
  from 1.437× to 1.142× bare metal, scale now FITS its reservation, and
  fibx overflows by 1.65 MB (6.5%) where the morning's gap was 8.6 MB.
  With slack alone both rungs are byte-identical to the bank -- correct
  but sized wrong still holds. A 1.65 MB shortfall is reservation-sizing
  territory, not narrowing territory.
- **whole's segfault IS finding 24, and MORE DECK MAKES IT GO AWAY.**
  That pairing is the most useful thing in this item. The crash is in
  `st_append_code` reading `st.workspace.code_capacity`, faulting at
  **0x9 = 1 + 8** where finding 24's recorded signature is **0x896 =
  2190 + 8** -- same function, same field, `workspace` reduced to a small
  integer. And with `cx_deck_slack` at 128 MB and nothing else changed,
  both rungs run byte-identical to the bank.
  So finding 24's "pointer-shaped length" is plausibly a CONSEQUENCE of
  deck exhaustion clobbering the record rather than an independent
  field-offset or struct-layout defect. **The decisive experiment RAN
  2026-08-21 evening and split the finding in half.** With
  `cx_deck_slack` at 256 MB the corruption is GONE -- the GP fault in
  `bsearch_rename_pos` never happens, so the trample mechanism is
  CONFIRMED -- but the run does not survive: it goes 6x longer (103s vs
  17.6s, 488 KB of IR emitted vs 12.6 KB) and then dies CLEANLY at
  `cx heap: exhausted at 1610611665 + 1725 of 1610612736`, the bump
  allocator's own 1.5 GiB ceiling. The instrument shows the deck at
  381 MB used against the 104 MB demand-lift-floor, climbing
  monotonically, no rewind ever (deck-exit keeping its position is
  faithful -- bare metal's emit-deck-exit-builtin stores r10 back to
  deck-pos-addr the same way). Bare metal compiles this same subject
  inside its arena (the banked fibx truth is the proof), so this arm
  allocates hundreds of MB inside deck brackets that bare metal does
  not. **Finding 24 is therefore NOT the emit rungs' 2 MB sizing story:
  the corruption half collapses into deck exhaustion, and the open half
  is a consumption divergence** -- what does this arm put on the deck at
  ~150x the volume? The copy-vs-alias family (substring/split/replace
  copies, list-constructor reservations, cx_new closure envs) is the
  suspect list. Numbers in JUSTIFICATIONS ("finding 24 slack
  experiment").
  (An earlier edit of this file said the opposite -- "deck exhaustion in
  disguise, not a pointer defect, do not put it on the finding-24 lead
  list." That was written from the bare `Segmentation fault at address
  0x9` line without reading the frame beneath it. The slack half was
  right; the dismissal was wrong.)
- All four emit rungs cluster at 27.0-27.1 MB across 3-61 defs
  (JUSTIFICATIONS); a ~2 MB bump to the formula's flat term covers every
  measured rung, and the sweep should then run 14/14 with no narrowing.
- The droplet sweep-prep gap is real: a fresh droplet sandbox carries no
  `ast/*.ir` and the sweep fails 0/14 in 71s. Unattended droplet sweeps
  (item 2.5) need the prep step to ship or regenerate the `.ir` files.

**Finding 24 -- CLOSED 2026-08-22, see item 1 below; the paragraph that follows is the 08-21 state kept for its exclusions.** The `codexir` crash on the 2.5 MB subject, which
now reproduces natively in 11 seconds instead of eleven minutes through
QEMU. Ruled out by measurement, do not re-test: use-after-reclaim (that
binary never calls `__heap-restore`), reuse of freed memory (free made a
no-op changes nothing -- run twice), the in-place concat, a wrong argument
(pointer identical at creation and use, length zero), the deck guard, an
out-of-buffer write (unchecked on BOTH arms, so upstream semantics), and the
0xAA fill (zero-filling changes nothing). The pointer-shaped-length lead is
CLOSED (2026-08-21 evening): slack removes the corruption, so the garbage
header was deck bytes trampling a live object, and pointer-shaped values are
simply what deck data looks like. The live lead now is VOLUME: instrument
which allocation paths run inside deck brackets and how many bytes each
contributes, on a subject size ramp -- if one family's deck bytes grow
superlinearly in subject size while bare metal's total stays inside the
lift floor, that family is the finding. Note also that the crossing guard
(`e4d2fcd1`) did NOT fire before the slack-0 GP fault -- main climbing back
under the deck after a restore is a trample direction the guard does not
see. The guard needs that direction, and a probe that triggers it.

**What remains before the PR, in order (re-pinned 2026-08-22 after the
census):**

1. **DONE 2026-08-22 -- the finding-24 volume hunt, answered in one
   session.** `deck_census.py` keyed every deck byte by (allocator call
   site, deck-record bracket): no family is superlinear, per-object sizes
   are bare metal's, and the 381 MB is eight uncompacted phases on a 2.5 MB
   subject. The "104 MB bare-metal floor" premise was our own harness's
   placeholder (`emit_harness.py` says so in its comment); the real driver
   reserves ~2.3 GB of per-phase decks with compaction between them.
   Finding 24 is CLOSED as a harness-sizing misread; findings README 24
   and JUSTIFICATIONS "deck census" carry the tables. Given a 2.5 GiB
   arena and 512 MB of deck, `native/codexir` compiles the fibx subject
   in 63 s, rc 0, and the IR matches the seed's up to def order, chapter
   title and a `ctd`/`record-ty` spelling.

   **What it leaves, DECIDED 2026-08-22 (Steve: "decide whatever"), to
   land after item 2's sweep:**
   - `emit_harness.py` DECK_PROLOGUE reserves a flat 512 MB instead of
     `demand-lift-floor` (measured need ~153 deck bytes per subject byte;
     381 MB on the fibx subject).
   - `cx_heap_reserve` 1.5 GiB -> 4 GiB. Lazily faulted since `c7feba61`,
     so no resident cost; RLIMIT_AS counts it (item 3).
   - Reword the flagship commit: "the hosted harness reserved one
     placeholder-sized deck for every phase; measured; no capacity
     divergence" replaces "MEDIUM, capacity diverges at scale".
   - Run down why the harness prints `record-ty` where the seed driver
     prints `ctd` for let-binding types (930 lines of the fibx IR) while
     the harness is open.
   - Finding 33 (tail calls) is item 1.7 below; finding 34 (hosted
     harnesses never reclaim) is folded into the harness edit if per-def
     brackets are cheap, else noted in the PR body.

2. **DONE 2026-08-22 -- the emit-rung flat term is 28 MiB** (`5c9948f6`
   on the branch, upstream's `X86_64Chapter.codex`, with its prose).
   Verified through the pipeline in a fresh sandbox: truths re-banked
   identical, four emit rungs byte-identical at slack 0. JUSTIFICATIONS
   "Landed as 4 MiB". The sandbox also found and fixed a ring-arm guard
   hole (`087d61a`): the verdict checked the TCP plug's fingerprint on
   ring rungs, which a fresh sandbox never has.
3. **The out-of-region absolute address question** (instrument work,
   still unanswered from the original design): what such an address
   means -- the SMP subjects peek ~2.1 GB against RLIMIT_AS caps that
   count reserved space, not resident pages. The census made this
   concrete: an 8 GiB thread-stack request was refused outright, and a
   2.5 GiB arena needed the AS ulimit raised to 3.3 GB before the
   reservation would even map.

Riding with whichever comes first: extend the `e4d2fcd1` crossing guard
to the main-from-below trample direction (measured miss 2026-08-21, and
now known to be exactly how finding 24's crash got past it), and
`probe-deck-overrun`, a zig-only labelled regression test that triggers
the refusal on purpose -- the one unit-test gap on the branch.

Sends after 76.

## 1.5 The unit tests -- INVENTORY COMPLETE 2026-08-21, keep it green

**Objective: instrument work that keeps turning into hunting.** Small Codex
programs, one per primitive tier, run on BOTH arms through the real
toolchains and compared. Ordered by what a failure invalidates rather than by
difficulty: if `__heap-save` does not observe allocation, every cost in every
other file is a zero that means nothing.

All seven tiers exist and carry both columns:

    tier 0/1  findings/prim-deck.codex       the meter, the two cursors    16 assertions
    tier 2    findings/prim-lists.codex      lists                          26 cost rows
    tier 3    findings/prim-text.codex       text, CCE, substring, split
    tier 4    findings/prim-records.codex    records and closures
    tier 5    findings/prim-buffers.codex    raw buffers
    tier 6    findings/prim-composite.codex  emit-all-defs in miniature      9 assertions

`findings/primitive-costs.md` is the cost table; `findings/probe-memory-model.codex`
carries the quadratic detector and predates the tiers. `prim-text-semantics`
pins what text MEANS rather than what it costs, as the before-picture for the
`Text` narrowing.

Small probes isolating one answer live beside them, and three exist because a
tier file could not hold the question: `probe-substring-trap` and
`probe-shift-count` each kill one arm on purpose, and `probe-deck-substring`
needs a rewind and a clobber to make its answer visible. Also
`probe-peek-qword`, `probe-fresh-span`, `prim-cce`.

**A tier file cannot assert anything that traps.** One trap takes the file's
other forty assertions with it, so a guarantee question gets its own probe and
the tier keeps the in-range rows.

**Ask whether a helper FAILS on the same inputs, not just whether it computes
the same answer.** Findings 28, 29 and 30 came from that question. A cold agent
has since swept the whole prelude for helpers that discard an argument or
return a bare constant and found **none remaining** -- `cx_heap_advance` and
`cx_heap_restore` returning 0 are FAITHFUL (bare metal's emitters end in
`li rd, 0`), and `cx_deck_enter`/`exit`/`set` are marked unchecked rather than
cleared. That question is now answered; do not re-run it.

**THE OPEN QUESTION THAT REPLACED IT: the plug fails in registers the census
cannot count.** Three separate findings today -- the type-variable leak
(`probe-tyvar-leak`), polymorphic `show` (`probe-show-types`) and `IrTry`
(finding 32) -- all fail as a raw zig error rather than a
`@compileError("zig plug: ...")` marker. Two mechanisms read only markers:
`zig-is-unmapped` decides recoverability by testing for one, and
`corpus_run.py --transpile` histograms them to rank which gap to fix first. So
each of these scores ZERO in the ranking that sets priorities, however often it
bites. Three instances in one day is a pattern, not three accidents, and the
systemic fix -- every unhandled construct refuses by name -- is worth more than
any of them individually.

**Coverage is chosen by counting, and the count now has a reachability column.**
`tier_coverage.py` reads the emitted `ast/*.zig`, not just the subject, because
IR emission prunes to what the `opening` reaches -- a quarter of
`whole-subject.codex` is dead in every rung built from it. A builtin heavy in
source and absent from every emitted rung is one **no rung can reach**, and a
unit test is the only thing that will ever cover it. `address-of` was 65 in
source and 4 emitted, which is why finding 31 sat undetected.

**What they found, in one day: findings 22, 23, 25, 26, 27, 28 and 29**, of which 25
was invisible to eleven days of rung sweeps because the ladder's own chapter
slugs coincide, and 26 and 27 were found by a test tripping over them before
anyone thought to look. Tier 6 would have caught defect A outright -- when
`__list-with-capacity` discarded its argument, "table survived 8 brackets"
would have said no, in about a second.

**Standing work, not a finished task.** Run the tiers after any emitter
change -- `tier_run.py <file>` does both arms and diffs them, and it banks the
bare-metal column, so only the plug's side costs anything after the first run.
Add a tier row whenever a finding names a primitive that has none.

Rules that make these worth the trouble. Codex whenever the property is
observable from inside a Codex program, so bare metal is the oracle; zig only
when it is not, and then it is a regression test with no oracle and must be
labelled so. Never print an address. Assert the instrument before believing
it -- every file checks its own meter against a known reservation. Keep a
control: `cat-accum` is quadratic on BOTH arms, so it is inherent to the
source and not ours, and without that column it would have been filed as a
plug defect. And where the arms legitimately differ, mark the lines and say
why rather than letting the file claim byte-identity it does not have.


## 1.7 Tail calls become loops -- the native loop's depth ceiling

**Objective: instrument work on the emitter that removes a ceiling
(finding 33); scheduled high by Steve 2026-08-22.** Every
`*-loop (xs) (i) (acc)` in the compiler is a self-call in tail position;
bare metal jumps (`st-set-tail-pos`), the plug calls, and Debug zig keeps
every frame. `zigemit` on the 13 MB fibx IR needs a >2 GiB thread stack
for 3.28M `tokenize_loop` frames. The emitter change: a def whose body's
tail positions are self-calls (same arity) becomes `while (true) {` with
parameter reassignment through temporaries; non-self tail calls stay
calls. Sweep `ast/allcycles.sh` after, rebuild the natives, and re-run
the fibx-subject chain (sandbox `20260822T014639Z-f24-volume` has the
subject and the numbers) as the proof: zigemit should get past
tokenizing on the stock 512 MB stack.

## 1.9 Update 49 is out -- the u49 ceremony, and PR 76's eight reds

**Objective: due diligence (the ceremony) that ends in a hunt (the
census).** Upstream `bdf0049b` is Update 49 and absorbed PR 76 (Steve,
2026-08-22). Order corrected by a cold read the same day (essay
random925): the census natives come from the BRANCH, so the rebase
precedes them. In order:

1. **Read `bdf0049b` first** (README step 1): `codex/plugs/zig/
   ZigEmitter.codex` against PR 76's branch (what the heap branch will
   conflict with), the seed hash, `codex/compiler/Emit/`,
   `tools/codex-vm.c`, `build/vm-config.ps1`. Nothing to delete for
   PR 76 -- its "workaround" was the eight-reds expectation, retired or
   refuted by step 6.
2. Pin branch `u49-rebank` at the release commit, zero cherry-picks if
   the ladder can run without any; push to the fork; `seed_identity.py`
   and `check_paths.py`; `droplet_vm_setup.sh` re-run (the pushed seed
   is stale on re-pin).
3. Tier bare columns (item 1.95's runner) -- seconds each, before the
   long run, banked under `findings/gold/u49/`.
4. `rebank_all.sh` in a sandbox (self-detaching; droplet venue if item
   2.5's prep gap is closed, else the laptop with the cold-agent brief).
   Bank `truth/u49` only over green zig arms; `bank_diff.sh` u48 -> u49
   is the Update's artifact. Re-pin `check_diags.py POLICY`; refresh the
   README timings and banked-against table; tag `u49-14of14`.
   **DONE 2026-08-22, tag `u49-14of14` at `aa5d0cc`:** droplet rebank,
   14/14, eleven truths byte-identical to u48, fibx/scale/whole moved
   only by the two new `port-*-16-block` builtins; census unchanged, so
   POLICY kept its pin. Steps 1-3 were done the same morning.
5. **Then** delete the deck-record rename from the four bundlers that
   still carry it (check, fib, desugar, lex -- Batch 2) and re-run only
   those truth arms on u49: a second, separate diff proves the rename
   image-preserving. Not in the same bank as the Update.
6. Rebase `zig-plug-heap-unification` onto the u49 pin (reword the
   flagship commit's Confidence paragraph while the hashes move anyway:
   finding 24 closed, no capacity divergence). Rebuild the natives from
   the rebased branch (laptop only; `native_build.sh` refuses the
   droplet). Tier zig columns. Then the corpus census: **the eight reds**
   -- stringbuilder-test, stats-wrap-test, validation-rules (char-CCE
   `ea8d51ac`), the carried text-fold-indexed differ, bloom-spread,
   consistent-hash-balance, particle-spread (`78e8da1b`) -- should all
   flip green; a survivor is a new finding.

## 1.95 The tiers run as a set, per Update -- BUILT 2026-08-22

**Objective: instrument work, done; keep it green.** `tiers_run.py` runs
every `prim-*` plus seven probes on both arms (five kill-an-arm probes
excluded by name with reasons), gold lives under `findings/gold/uNN/`
(u48 banked: 19 columns), and `findings/gold/EXPECTED.txt` is the
ledger of known disagreements -- 66 rows, every one a cost row from
primitive-costs.md or an open finding (19, 20, 25). First full run:
10 green, 9 noted, 2.5 minutes. The `??` marker (a ledger row whose arms
agree) fired on its first run and caught a key collision, which is what
it is for. README steps 3 and 5 carry the ceremony slots. What the ledger
says to watch on u49: the three finding-19 rows should flip to `STALE`
when the branch rebases (PR 76 absorbed) -- delete them then.

## 2. The external review, in three batches

**Objective: instrument work.** The review's high findings are wrong-bank
and wrong-PASS closers -- ways the harness could lie green. None of it
hunts; all of it decides whether a hunt's verdict can be trusted.

`REVIEW-2026-08-19.md` (Marley, for Damian, at our 8a74c94) -- ~34 findings.
The three high ones we spot-checked all confirmed. Several have since been
fixed in passing (banking provenance, ring_compile's pre-READY EOF); each
batch's first act is re-checking its list against the tree:

- **Batch 1, keyboard-only:** the wrong-bank and wrong-PASS closers plus
  unattended hazards -- `plug_run` truncation-reads-as-success, QEMU
  orphan try/finally, rm-stale-artifacts-first family, checks that
  report but do not refuse, small correctness (f4_boot, plugcycle,
  seed_identity label, pcap coverage), doc seams. Commit per finding.
- **Batch 2, needs QEMU + a re-bank:** delete the deck-record rename from
  the ten bundlers (workaround-hygiene; Update 43 closed the finding) and
  let the bank diff prove it image-preserving; unify the two plug
  fingerprint guards on the ring model.
- **Batch 3, structural, its own session, net first:** `tests/` for the
  refusers, THEN driver consolidation into codex_vm and the
  harness/bundler dedup.
- Declined or deferred, with reasons in the review response: tracked
  census json stays; LICENSE is Steve's call; errors='replace'
  byte-compare rides Batch 3.

## 2.2 The sweep consumes IR it does not create -- GUARDED 2026-08-21

**Objective: instrument work, and the wrong-PASS kind.** Found 2026-08-21
when a sweep was launched in a fresh sandbox and every rung died instantly:
`allcycles.sh` reads `ast/<rung>.ir` and does not produce it. Those files are
truth-arm output. In the shared checkout they persist from whatever ran last,
so the dependency is invisible; a fresh worktree has none, which is how it
surfaced.

**The hazard is not the crash, it is the silence.** Nothing verifies that a
`.ir` came from the branch and seed now under test. The 22 files sitting in
the droplet checkout when this was found were generated by the GAPS-branch
sweep at 02:42, and were about to be used for a HEAP-branch sweep. If a stale
`.ir` survives a branch or seed change, the zig arm transpiles yesterday's IR
and compares it against today's bank -- a green that means nothing. That is
the same failure the provenance sidecars already guard for banked truths
(`truth_prov.py`), applied to the wrong artifact.

**Done.** The truth arm stamps `ast/<unit>.ir.prov` the moment the IR is known
good, and both `zig_arm` and `ring_arm` refuse before spending a transport --
so the refusal names the rung about to be judged instead of surfacing as a
bank mismatch hours later, or not at all.

The key is **(seed sha, subject bytes, mode flags)**, which is exactly what
the IR is a function of. Not the Codex checkout's HEAD, which was the first
shape proposed here: the plug does not participate in producing IR, so
keying on HEAD would refuse on every plug commit -- every commit that cannot
possibly have changed the IR -- and a guard that cries wolf gets switched off.

**One-time cost, and it lands on the next sweep.** Every `.ir` predating the
guard is refused as UNPROVENANCED, because there is no record to check and
inferring one from timestamps is the failure `truth_prov` already refuses for
truths. Regenerating is one `ring_compile.py ast/<unit>-ir-cce.blob
ast/<unit>.ir` per unit plus a `stamp-ir`, not a full truth arm -- and only
two units cover all four emit rungs, since `scale` rides `fibx` and `clamp`
rides `whole`.

Still open from the original item: `allcycles.sh` should REGENERATE a
refused `.ir` rather than stopping, so a fresh worktree bootstraps itself.

## 2.5 The droplet becomes a full venue (DECIDED 2026-08-20 late, Steve)

**Objective: instrument work.** The appliance model dies of its own
elegance: the held ssh ties every droplet job to the laptop's wifi, and
today's blip cost a rung. Full checkouts + toolchain on the droplet
means long jobs run AND SURVIVE there, laptop-free. Gopher stays
protected by the same rails (nice, the compute lock, 1300 MB guests,
untouched home dirs).

DONE tonight: git (present), pwsh 7.5.4 at ~/.local/pwsh (the laptop's
path -- scripts run verbatim), both repos cloned (~/showell_repos/*,
NR on the verbatim pin), check_paths green mod cycle-built artifacts,
and **the lex truth arm ran end to end on the droplet, byte-identical
to the banked u48 truth** -- venue-independence of the truth pipeline
is measured, not assumed. Remaining, in rough order:
- zig 0.16.0 (tarball to ~/zig-0.16.0, mirroring the laptop path) --
  unlocks zig arms, natives, censuses droplet-side.
- ~~Push credentials~~ DECIDED (Steve): the droplet is FETCH-ONLY --
  it holds no git credentials, pulls the public repos anonymously, and
  results come home by scp; commits and pushes stay laptop-side. The
  cleanest trust posture beside the live site, revisit only if it
  chafes.
- Detached-job discipline droplet-side (the rebank self-detach pattern;
  tmux or setsid, logs in the droplet ladder's logs/). DONE 2026-08-21:
  `PHASE_FROM=C nice -n 15 setsid nohup ./overnight_verify.sh > log 2>&1 &`
  survives the ssh going away. Caution: do not let the backgrounded chain
  inherit the ssh session's stdout, or ssh holds the channel open and
  looks hung while the job runs fine.
- **MEASURED LIMIT 2026-08-21: the droplet runs SWEEPS but not NATIVE
  BUILDS at CODEX_MEM_MB=1300.** The gaps sweep went 14/14 green, then
  phase D stalled compiling zigemit to IR through the seed: QEMU burned
  4 seconds of CPU in 28 minutes with both it and `ring_compile.py`
  parked in `do_poll` and both chardev sockets ESTABLISHED -- the guest
  ran briefly and stopped. Same silent-death class as the TCP plug's
  measured 1600 MB floor. Note `ringplug.cdx` (237865 bytes) DID build
  in that same phase at the same cap, and zigemit is 236876 bytes, so
  this is about what the seed's IR compile costs, not blob size; the
  floor is not bisected. Diagnose stalls by CPU TIME, not elapsed --
  `ps -o etime,time` separates "slow" from "dead" in one line.
  Consequence: censuses and native builds stay laptop-side until the
  floor is measured. Raising the cap toward 1600 on a 1968 MB box that
  also serves the live site is not something to gamble unattended.
- CODEX_MEM_MB=1300 / CODEX_ACCEL=tcg defaults for droplet sessions
  (a droplet-local env file the scripts source, not per-command
  ceremony).
- README venue sections rewritten when the model settles. BOTH modes
  persist, deliberately (Steve, 2026-08-20): **the venue follows the
  mode.** HUNTING stays local or hybrid -- the straw scripts
  (droplet_compile/droplet_transpile, the two-venue sweep) are the
  keyboard-tempo tools and are NOT retired. DUE DILIGENCE moves
  all-on-droplet -- long unattended runs must survive the laptop
  leaving the wifi. The full-venue checkout and the appliance straw
  coexist on the same box; the compute lock is the arbiter as ever.

## 3. Provenance watches one file too many

**Objective: instrument work.** The truth sidecars hash `oracle_lib.sh`
whole, so a guard-or-comment edit to the ZIG-arm half invalidates every
recorded truth's provenance -- it cost a full truth-arm re-measurement
on 2026-08-20, hours after the same session built the guards that fired
(the wiring batch edited oracle_lib between recording and banking; the
diff was provably guards and comments, and the only honest path was
re-measuring). Fix shape: segregate by volatility -- split the
truth-arm measurement machinery (mode_flags, truth_arm, split plumbing)
into its own sourced file that the sidecar watches, leaving the
zig-arm/instrument half free to move. Do it right after a bank lands,
never between recording and banking.

## 4. Widening the hunting ground: the gap families

**Objective: hunting, reached through our own gap-filling.** The census
buckets with oracles left to consult are all blocked on OUR gaps; every
family implemented promotes a slab of programs into the comparing stage
where the depot's oracles can finally see them (random895 -- gap work is
not port-finishing, it is instrument reach).

**BATCH IMPLEMENTED 2026-08-20 evening** on branch
`zig-plug-refusal-gaps` (off the PR-76 tip; nine commits; typecheck
meter: 90 of the census's 105 refusals promoted). In it: the entry
shim (startFn, 39 refusals), Boolean->Integer coercion at declaring
boundaries (35), the memory-access family to C#'s _Buf rules
(alloc-bytes, peek/poke-16/32, poke-byte, bit-not -- the marker slab's
top), unit aliases (finding 17), the approx-eq 4-ULP band (finding
20), @"..." identifier quoting (ident-letters), Boolean literal
patterns, and the observed prelude-shadowing colliders. Verification
= overnight_verify.sh phases C-D (sweep + census); the PR follows it.

Residual classes, measured, for the next batch:
- **Curried/oversaturated calls** (5): a zero-param def whose value is
  a closure called with args needs `f().call(...)`; struct-vs-struct
  binops in the fork/par family ride the same machinery.
- **show of a Real** (2): needs bare metal's __show_real formatting
  mirrored, never guessed.
- **Type-class dictionaries** (2): undeclared `T2`.
- **The systematic prelude-shadowing sweep** (1+): zig bans locals AND
  params shadowing file-scope names; dns-answer-count defines l, base,
  h... -- rename every prelude local and param to cx_, mechanically,
  in one commit. Letter-chasing measured futile.
- **MkTup2 out-of-unit** (16 markers): tuple machinery works when
  Tup2 is declared in-unit; the marker is the type arriving from
  outside. Drags ctor-map + pattern arms; own item.
- One-offs: `sin` (math builtin), one non-exhaustive switch.
- **From the batch's cold review (2026-08-20 late)**: the `@"..."`
  quoting breaks where a name is EXTENDED after sanitizing
  (`zig-sanitize(name) & "S"` gives `@"Name"S`; `_arg_` + raw ident
  ships hi bytes bare -- the file's own comment predicted it); f32
  approx-eq needs bare metal's distinct f32 ordinal path (the current
  band is f64-only, effectively zero f32-ULPs); and IrApproxEqExact
  as `==` diverges from ordinal-distance-0 on same-bits NaN (oracle 1,
  zig 0) -- the last two are register candidates, not just fixes.

Still queued from before:
- **Real-literal candidates in the other plugs** (source-read only,
  2026-08-19): the JS emitter's IrNumLit is `Number(BigInt.asIntN(64,
  bits))` -- bits as a NUMBER, not a bitcast; and parseFloat /
  double.Parse are correctly-rounded where bare metal's
  __text_to_double is not. Probe before filing either. Same family as
  finding 18's asides (python overflow, C# IrPowInt-as-XOR, the missing
  overflow oracle row).

## 4.5 Execute the rung renames (PROPOSED 2026-08-21, not started)

**Objective: instrument work.** The rung names bury the lead -- `fibx` says
nothing about what it tests and `scale` names a property of the input. Worse,
six of fourteen rungs never reach the x86 back end at all and nothing in the
names says so. The full proposal, mapping and migration plan is
`RENAME-PROPOSAL.md`; that file is temporary and gets deleted by the commit
that executes it.

Headlines: a unit is named for the stage it reaches, a rung adds
`_on_<subject>` only when its unit carries two subjects, and **six names do not
move**. No re-bank is needed -- no rung name appears in any banked truth as a
rung name, so the 42 files move by `git mv` with their bytes unchanged.

**Do it when the deck investigation settles, not before.** Every finding
written this week refers to the current names, and renaming while we are still
re-reading them costs more than it saves.

The one hazard worth carrying in your head: all `ast/` outputs are gitignored,
so after a rename the tree still holds a complete set of real, plausible,
pre-rename artifacts under the old names. Three sites spell old names as
literals without deriving them from `LADDER_RUNGS` -- `ast/f3_run.zig:222`,
`ast/f4_boot.py:26-29`, `overnight_verify.sh:99-100` -- and a missed one reads
yesterday's dump and passes green. Clean the orphans before the first sweep.

## 5. Diagnostics as a banked set

**Objective: instrument work.** A pinned count says something changed; a
banked set says what. Diffed like a truth file, retiring the
CDX6020-style count pins that move whenever the unit list changes rather
than when the source does. (The sweep's own census note says exactly
this every time it prints.)

## 6. Parked: the notebook / Prism angle

Not work, a bookmark, deliberately last. A Python-hosted notebook showing
how Codex source becomes assembly, stage by stage, is a weekend-sized
demonstrator of Damian's dusty **Prism** design
(`apps/prism/design/Active/PrismDesign.md`). The native loop and `zigc`
already are its core machinery in cheap form. If picked up, re-read the
design against what exists now and ask Damian what he would want first.

Also parked, the endgame framing (random839): piggyback the C# DDC
witness path with zig -- C# stops at "compiles", zig RUNS.

---

## Outbound queue

**LIVE: PR 76** (damiant3/NewRepository/pull/76, sent 2026-08-20): wrap
arithmetic, shadowed-builtin yield, char-CCE migration -- the hunt
three, off `b643e7c`, spot-verified 5/5 against U48's own oracles.
Carries the source-read asides and offers the overflow oracle row.

Queued behind it: the heap unification (item 1, branch
`zig-plug-heap-unification`, commits reworded with per-commit Confidence
paragraphs 2026-08-21; verified by the 10/12 sweep, the tiers, and the
full-corpus census with zero regressions; still owed before it sends:
the emit-rung flat-term bump, the finding-24 volume hunt or an honest
open-issue note, and the out-of-region answer below). Base for anything
new:
whatever the current release is when it goes; absorption is a content
question, never a patch-id question. PRs 71-75 are absorbed --
one line each in DONE.md.

---

## How to read this list, given how the work actually goes

Two modes alternate: at the keyboard, where decisions and code happen, and
away from the machine, where something long should be running unattended.
**Keyboard work** is the probes, emitter changes, and tooling fixes; **away
work** is running what those produce: the rebanks, the sweeps, the census
runs. A hunt's *runs* are away work; its *reads* are not.

The rule that makes both work: **one compute job per host.** The laptop
holds one QEMU comfortably; the droplet is flocked inside its wrappers
and every laptop entry point takes `take_compute_lock`. The droplet
venue means away work can overlap keyboard work across hosts -- but
never two compute jobs on one.
