# Two cold reads of the README, 2026-08-27 — what was applied and what was not

Two fresh agents, run serially, neither given the other's findings.

**Pass 1** read the README *alone* (plus the upstream front page) and asked
whether a stranger can orient. **Pass 2** got the whole ladder tree and asked
whether the document describes the system that exists.

Both are worth keeping for the same reason: the applied fixes are in git, but
the *reasoning* about what was left, and why, is not recoverable from a diff.

## Applied

**From pass 1** — a front door. The title spent line 1 on `phase-oracle`, a
term used once and never again. 27 of the first 31 lines were provenance
metadata. The parent project was named at line 1035 and given a URL at 1096.
And the naming was *wrong*, not merely late: we called the parent "the Codex
repository", which is the old name — Codex is the language, Cobblestone is the
project, so a newcomer searching GitHub found nothing. Fixed at first use.

**From pass 2** — the drift, all verified against the code before writing:
the banked-against table named a superseded interim bank; the fresh-clone
runbook sent a newcomer to a 39-minute rebank that `restore_truths.py` had
made unnecessary; the `zigc` Open Question was answered by `zigc_verify.sh`;
the watched-set paragraph omitted `truth_prov.SHARED`, which is the whole
reason the plug arms live in `plug_arm_lib.sh`; `arm_for`/`zig_verdict` were
cited to the wrong file four times; fib is in nine generators with a divergent
tenth; and five instruments existed that the README had never heard of.

## NOT applied — decisions, not oversights

**The license.** There is none, anywhere, for this repository or for the
vendored `seed/Codex.cdx` — and the seed is Damian's artifact sitting in our
tree. Pass 2 called it the only *legal* gap in the document. **Steve's call,
not mine.**

**Reordering "What the check proves, and what it does not"** from 44% depth to
just after "Why this exists". Zero words, pure gain, and pass 2 called that
section "the best epistemics I have read in a README" — it argues against its
own headline claim. Left because it moves a large block and wants eyes on the
result.

**`ast/repro-mid.codex` in the zigc transcript.** The file has never existed
and is gitignored. Recorded in the Open Question rather than silently
repointed at `ast/repro.codex`, because which subject that transcript actually
measured is a question, not a typo.

**The banked-against table's final state.** Corrected to u50, which is what is
banked *now*. It needs one more edit to u51 when the running rebank lands;
`check_paths.py` prints a WARN naming exactly that debt.

## The lesson about how I briefed them

I told pass 2 that pass 1's findings "were applied to the first 32 lines", to
stop it re-treading orientation. The stale banked-against table sits at lines
36-40, immediately below that boundary. Pass 1 *had* read those lines — and
reported them as "27 of 31 lines of provenance metadata", a comment on their
PLACEMENT.

**Neither agent was asked whether the most prominent claim in the document was
true.** Pass 2 caught it by disregarding my scoping, and said so.

"Already reviewed" is not "already checked", and a scoping instruction is a
place where the briefer's assumptions become the reader's blind spot. Both
passes were told to push back on the brief; both did; only one of those
push-backs was about the brief being wrong in a way that mattered.
