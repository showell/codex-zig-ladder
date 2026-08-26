# SENT — awaiting the settling measurement

**Sent by Steve over Gmail 2026-08-26 ~23:0x.** It withdraws our previous
report outright and promises them the bare-metal result either way.

**WE NOW OWE THEM A NUMBER.** The measurement is the same probe through
the SEED, and it is queued behind the running sweep. Whichever of the
three outcomes lands, it gets reported -- including outcome 3, where our
own re-run refuses and the first run was simply contaminated. That is the
outcome that would be most embarrassing and it is the one we are most
obliged to send, because we have already asked them to stop looking.

They asked for our exact pin before either side concludes anything.
Time-sensitive: they are blocked on us.

---

## The reply

Here is the pin, and ahead of it something that probably explains your
non-repro without needing the pin at all.

**We measured with the wrong compiler.** The tool our probe runs against
is `native/codexir`, and it is not the reference compiler — its own build
script describes it as "bundle the subject, compile it to IR with the
seed, push that IR through the ring plug, and build the emitted zig." It
is the compiler *compiled through our zig plug*. Every diagnostic in that
probe run came out of a type checker our own backend emitted. We reported
a soundness hole in your checker on the strength of our arm disagreeing
with your arm, without checking which arm we were standing on. That is
our error, and your asking for the pin before concluding was the right
instinct — we should have had it first.

**The pin, as requested:**

- codex tree on branch `zig-plug-tvar-not-an-answer`, probe run at
  `31be533e`
- that is 11 commits above `upstream/master` = `8cc80685` (Update 50)
- **all 11 touch `codex/plugs/zig/ZigEmitter.codex` and nothing else** —
  no compiler, no type checker, no seed
- natives built from that tree by `native_build.sh`, i.e. seed → ring
  plug → emitted zig → `zig build-exe`

So if your seeds refuse `fa (x) (y) = let g = fa in g x` with CDX2001 at
four revisions back to 2026-08-20 — and your full-arity positive control
compiles at all four — then on the most likely reading the difference is
not in the checker at all. **It is our plug miscompiling your type
checker until CDX2001 stops firing.**

That would be ours, and it is worse than what we reported: a silent wrong
answer in the compiler we build, which is the exact class this ladder
exists to catch and the one we would least like to be sitting on.

**We are running the settling measurement now**: the same program through
the seed on bare metal, which is the arm we should have used in the first
place. Three outcomes and we will report whichever lands —

1. bare metal refuses, ours accepts → ours, a silent miscompile of the
   checker, and we will have a reproducer for you.
2. bare metal also accepts → the pins genuinely differ and the question
   is which revision changed.
3. our own re-run refuses → the first run was contaminated and it is
   neither.

Until then, **please treat our previous report as withdrawn** rather than
as a finding awaiting confirmation. We would rather you spend no more
time on it than we have already cost you.

One thing that does survive either way, and is why we are not simply
embarrassed: the probe was written with its prediction recorded before it
compiled, which is what made the surprise legible instead of arguable.
The prediction was wrong, the conclusion drawn from it was wrong, and the
apparatus still did its job — it just pointed at us.

---

## Notes for Steve before sending

- **My recommendation is to send this now, not after the measurement.**
  They asked for the pin explicitly and are waiting on it; the pin is a
  fact, and the instrument error is information they need to interpret
  anything we already said. Holding it for ~30 minutes leaves them
  possibly spending time on a non-issue that is ours.
- It withdraws the report outright rather than hedging it. That is the
  right shape when the instrument is in question — "awaiting
  confirmation" would invite them to keep looking.
- It does not promise which of the three outcomes will land.
