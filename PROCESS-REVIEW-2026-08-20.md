# Process review, 2026-08-20 (cold agent, for Steve + Claude)

A cold agent read README.md / PRIORITIES.md / DONE.md against the repo
mid-ceremony and evaluated three objectives: staleness prevention,
decision simplicity, crash resilience. Findings verbatim below;
disposition notes in [brackets] added on triage.

## Staleness

- **S1 (high)** Step 5's "re-measure timings every rebank" points at
  logs that carry no timestamps; only sweep_lib's rung_stamp clocks
  anything. Fix: rung_stamp into oracle_lib, called from both loops,
  one elapsed line at the end. [wiring batch]
- **S2 (high)** Log evidence untracked/unindexed; the u47 14/14 claim
  traces to two logs nothing names; six ad-hoc naming conventions.
  Fix: annotated tags carrying log name + sha + count, or a tracked
  logs/INDEX.md. [INDEX.md created now; tag policy adopted at u48]
- **S3 (medium)** README promises three banks by name; bank_truth
  prunes to --keep 3 silently. Fix: describe the policy, not the
  enumeration. [done now]
- **S4 (medium)** The bank-diff loop hardcodes u46/u47 and is cited
  from PRIORITIES. Fix: bank_diff.sh defaulting to the two newest.
  [done now]
- **S5 (medium)** Orphan executables (tonight.sh, recon.sh,
  verify_merge.sh, run_bag_probes.sh, ast/irmemcycle.sh) have no
  retirement rule. Fix: extend workaround-hygiene to scripts; delete
  tonight.sh in the commit that closes finding 15. [queued at item 1.4]
- **S6 (low)** Register headline is hand-counted. [accepted as-is]
- **S7 (low)** Banked-against table has a derived counterpart nothing
  cross-checks. Fix: check_paths warns on mismatch outside a rebank.
  [wiring batch]

## Decision simplicity

- **D1 (high)** "Bank" means both the working golden files and the
  tracked truth/uNN artifact; rebank_all prints "all banked" without
  ever running bank_truth. Failure story: a post-crash session tags
  14/14 over a bank never taken. Fix: "recorded" for the working
  sense; allcycles success path prints NOT BANKED. [prose done now;
  print lines in wiring batch]
- **D2 (high)** No precedence rule between PRIORITIES and README; the
  two order the ceremony differently. Fix: one sentence -- README is
  the step list, PRIORITIES adds items and says where they slot.
  [done now]
- **D3 (medium)** take_compute_lock guards only the sweep trio; the
  in-flight rebank holds nothing, so the lock reads as protection it
  is not. Fix: lock in oracle_lib, taken by rebank/allcycles too.
  [wiring batch; sweep_lib's lock hardened NOW with a process check
  so the trio cannot start beside an unlocked legacy job]
- **D4 (medium)** The detach incantation lives outside "Running it".
  Fix: rebank_all logs and detaches itself. [pointer added now;
  self-logging in wiring batch]
- **D5 (low)** The capacity-vs-correctness pin rule wants a PIN.md on
  the pin branch. [DECLINED: a PIN.md commit would itself make the
  ideal-zero pin nonzero; the banked-against table now carries the
  release hash, so `git log <hash>..HEAD` in the checkout IS the
  check, one command, no artifact]

## Crash resilience

- **C1 (high)** Detached runs die indistinguishably from running;
  no EXIT trap, no summary line. Fix: traps + "SWEEP: n/14" line.
  [wiring batch]
- **C2 (high)** Nothing on disk says where in the ceremony you are.
  Fix: ladder_status.py deriving state (seed/update, banks, tags,
  truth prov freshness, lock/process state, newest log). [BUILT NOW —
  also the reviewer's own IF]
- **C3 (medium)** --force's destructiveness (subset REPLACES the full
  bank) is documented as a convenience. Fix: README warning line +
  a ready-count confirm in bank_truth. [warning done now; confirm in
  wiring batch]
- **C4 (medium)** Mixed working tree (two truths still u47, no prov)
  is caught only at bank time, hours late. Fix: zig_verdict consults
  the prov sidecar and refuses per-use. [wiring batch]
- **C5 (medium)** seed_identity.require_match exists, nothing calls
  it. Fix: call at truth_arm top and after split_truth. [wiring batch]
- **C6 (low)** Stale editor swap on PRIORITIES.md. [self-resolved]

## What already serves the objectives well (preserve)

The rung/unit cross-check at source time; truth_prov sidecars;
bank_truth's temp-dir+rename and empty-set refusal; the silence rule;
check_diags' pinned populations that fail the sweep; seed_identity
deriving the label from the seed's own hash; CODEX_ROOT's refusal to
guess; the mid-rebank table-lag paragraph; the Objective/mode lines;
the README's willingness to record its own violations.
