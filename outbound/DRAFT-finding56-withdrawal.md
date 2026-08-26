# Draft: the settling run, and a full withdrawal — for the compiler lane

Not sent. This retracts both of our claims, not one.

---

## The reply

The settling run is in and the answer is neither of the outcomes we
offered you. **Nothing is wrong with any compiler. Our instrument was
deaf.**

One tree, one source unit, three arms:

```
program              seed (bare metal)     native/codexir   native/codexzig
probe-pr87-alias     CDX2001 Int vs Fun    rc=0, no diags   CDX2001 Int vs Fun
probe-pr87-direct    CDX2001 Int vs Fun    rc=0, no diags   CDX2001 Int vs Fun
probe-cdx2001-text   CDX2001 Int vs Text   rc=0, no diags   CDX2001 Int vs Text
```

`codexir` and `codexzig` are **the same compiler, emitted by the same
plug, from the same tree.** They differ only in the harness wrapped
around them. Ours merges the diagnostic bags and halts in one and does
not consult them at all in the other: `CodexIrHarness.codex` calls
`check-chapter`, binds `cr.state`, and contains the word `bag` zero
times. The checker computed CDX2001 every time. One harness never asked.

**So both of our claims are withdrawn:**

1. Codex's type checker is not unsound. Your four-seed sweep was right,
   and it was right for the reason you gave.
2. Our plug does not miscompile your type checker. `codexzig` is that
   same plug's output and reports your diagnostic with your code and your
   wording, on both shapes.

The second withdrawal is the one worth dwelling on, because we sent it to
you with some confidence eight hours into a good day. It was refuted by a
tool we already had, that we could have run at any point, that takes four
seconds.

**Your literal-pattern pointer was sound and we should say what it did.**
`when-bool-cross` and `when-bool-pattern` are green on that tree, so you
correctly ruled out the mechanism you named. We narrowed your claim in a
draft we never sent, on the grounds that leaf-program controls do not
speak for a whole checker — that narrowing was right in principle and
irrelevant in fact, because there was no miscompile to find. Your
instinct to name a mechanism and give us a cheap way to test it is what
we would like more of, not less.

**What was actually broken is ours and we had already filed it.** Our IR
harness's missing error gate is a finding we wrote up the same morning,
left open, and then used all night as an oracle. It is now the top item
in our queue, and not as a tidy-up: our corpus runner uses that same
harness, so a corpus program carrying a compiler error emits IR anyway
and we build and score its output. We do not currently know how many of
our 326 "clean" programs are in that state. The gated harness found 41 of
593 when we switched its gate on; the ungated one has never been asked.

**What we owe you and are not sending:** a reproducer, because there is
nothing to reproduce.

**What the exchange cost you:** a triage round and a four-seed sweep. We
are sorry for that specifically — you asked for our exact pin before
concluding anything, which was the right instinct, and the thing your pin
request would have caught is the thing we then failed to check twice
more.

**What it bought us**, for whatever that is worth on your side: three
wrong attributions in one evening, each killed by the next measurement,
and a rule we did not have this morning — the arm that answers a question
has to be named in the answer. You put it better: read the kernel line it
prints.

---

## Notes for Steve before sending

- This retracts BOTH claims. It does not try to salvage a smaller finding
  from the wreck, because there isn't one.
- It credits their pointer and their pin request rather than glossing
  them, and it names what the exchange cost them.
- It does NOT dwell. One apology, specific, then the facts.
- The corpus-integrity consequence is included because it is the real
  finding of the evening and it is honest about not knowing the number
  yet.
