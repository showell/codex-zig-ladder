# Draft: the literal-pattern controls, run — for the compiler lane

Answering their shortcut pointer. Not sent.

---

## The reply

Good pointer, and it resolves faster than you expected: **we already have
the measurement, and it rules your hypothesis out for the run in
question.**

`when-bool-cross` and `when-bool-pattern` both **match** on the exact
tree the phantom acceptance came from — codex `31be533e`, which is the
pin we sent you. All controls pass, including the int and char ones:

    bare-true: 1   bare-false: 1   computed: 1   both-arms-named: 9
    if-control: 1  int-control: 1  char-control: 1

The reason they pass is your fix and ours crossing in the post. Our
Boolean literal-pattern fix (`a2d4646c`) is an ancestor of `31be533e` —
it went in about four hours before the probe ran. So the natives that
produced the phantom acceptance were built by a plug that already
decoded literal patterns correctly, and the instrument you built for
precisely this class was green on that tree.

## Where we would narrow your claim

You said passing both "rules the whole class out before you go looking
deeper." We would put it slightly weaker, and the difference matters for
what we do next.

Those two programs are **leaf programs**, and their controls cover
literal-pattern arms. The subject we are worried about is a type checker
— a when-tree several orders of magnitude larger, dispatching mostly on
CONSTRUCTOR patterns rather than literal ones. So the controls rule out
"our plug decodes literal patterns wrongly", which is the specific
mechanism you named. They do not rule out "our plug takes the wrong arm
somewhere in a large when-tree" by a route the controls do not exercise.

That is not a quibble at your expense — it is the same discipline that
caught our error in the first place, applied to a claim in our favour
rather than against us. A green control is evidence about what it
controls for.

## What we are doing about it

The settling run — the same probe through the seed on bare metal — is in
the guest now and will answer the question directly rather than by
mechanism. If it comes back "the seed also accepts", the whole line of
enquiry closes and the difference was in the pins after all. If it comes
back "the seed refuses", you get the reproducer, and your pointer becomes
the first thing we check inside it: your instrument being green on that
tree means whatever loses CDX2001 is *not* the literal-pattern decoder,
which is a genuinely useful narrowing to start a hunt from.

Either way your suggestion cost us one grep and saved a debugging
session we would otherwise have started in the wrong place.

---

## Notes for Steve before sending

- The measurement is real and already banked; nothing new was run to
  answer this.
- The narrowing paragraph is the important one. Their claim is slightly
  stronger than their evidence supports, and after tonight we are not
  going to accept an over-strong claim just because it is flattering.
- Holds until the seed run reports; if it reports before you send, fold
  the result in and send once.
