# What the zig ladder saw in Update 52, and what it could not see

*Draft. Written by Claude, on Steve Howell's account and at his direction.
Update 52's ceremony findings, apart from the duplicate-arm defect already
sent as PR 96.*

---

## Summary

Three things, in descending order of how much they should worry anyone.

1. **Structural equality on a composite is a silent wrong answer in the zig
   plug.** Bare metal compares by contents; the zig plug compares by identity.
   It compiles, runs, and prints a plausible answer. **This is our gap, not
   yours** -- we are reporting it because Update 52 widened it and because the
   shape may not be unique to zig.
2. **Neither of Update 52's headline compiler changes is reachable from our
   rung population**, measured rather than assumed. That is a statement about
   the limits of our evidence, and it is why our sweep was quiet where you
   might have expected noise.
3. **A small request about release-note spelling**, which costs you nothing
   and saves anyone automating against the notes an afternoon.

## 1. `==` on a composite: contents on bare metal, identity through the zig plug

**MEASURED.** `findings/probe-recursive-eq.codex`, in our tier set, both arms
at the Update 52 pin `968d4600` (with PR 96 applied, or nothing builds):

    row                          bare metal   zig plug
    equal shape, two objects     yes          no      <-- disagrees
    different shape              no           no
    a value compared to itself   yes          yes
    equal shape, nested          yes          no      <-- disagrees
    different shape, nested      no           no

The two agreeing rows are the diagnosis rather than noise: a pointer
comparison gets "different shape" and "a value compared to itself" RIGHT, so a
probe carrying only equal-shape rows could not have told identity from a
broken structural compare. These rows say which it is.

**Why Update 52 is where this surfaced.** Before it, the x86 back end refused
`==` on a self-recursive sum outright -- `cdx-recursive-structural-eq`, "this
backend compares a sum by inlining a field compare", and inlining has no
correct bound. Update 52 replaced the refusal with a synthesised
`__eq_<Sum>` helper, called rather than inlined, so the recursion terminates
at runtime on the data. Confirmed by symbol: `__eq_Tree` appears exactly once
in the probe's emitted CDX map. **A program asking this question did not
compile before Update 52**, which is why no tier covered it.

**The plug side is a one-line cause.** `emit-zig-binary`'s `IrEq` arm
special-cases Text and otherwise emits raw zig `==`; the emitted line is
literally `(a_ == b_)`. Every record is a pointer in that plug, so `==` on a
composite is identity.

**Closing it is real work, which is why this is an issue and not a PR from
us.** It means giving the emitter a structural path with a synthesised
recursive helper, mirroring what `X86_64.codex` just gained. We expect to do
it; we are not asking you to.

**The part worth your attention: we do not think recursion has anything to do
with it.** `emit-sum-structural-eq` predates Update 52, so bare metal has
compared non-recursive sums structurally all along, and the zig plug's raw
`==` has answered by identity all along. If that is right, Update 52 did not
create this divergence -- it only widened it to a case that previously
refused, and the older and larger half has been invisible the whole time
because **no tier in our set compares two composite values.** Every `==` in
every tier we have compares a scalar: a list length, a field, an integer.
`findings/probe-composite-eq.codex` is written to settle it.

**Worth checking on your side:** whether any plug in the fleet that represents
composites as references has the same answer, and whether your own battery
compares two structurally-equal composite values anywhere. We could not find a
test for the recursive path in `codex/test/` -- Update 52 added
`show-partial-application` and four desk/app cases, and nothing that exercises
`__eq_<Sum>`. That may simply mean it is covered somewhere we cannot see.

## 2. What our sweep could NOT see, stated so our quiet is not mistaken for a clean bill

**MEASURED.** Across the twelve compiler-chapter subjects our rungs compile:

- **Zero `__eq_` symbols** in any subject's CDX map. Update 52's headline
  codegen change never fired anywhere in our population.
- **Zero CDX2052** in any subject's diagnostics. COMPILER-31's new refusal
  never fired either.

All fourteen truths came back byte-identical to the Update 51 bank. The honest
reading of that is **not** "Update 52 changed nothing" -- it is "Update 52's
changes lie outside what twelve compiler-chapter subjects exercise." We
mention it because a green DDC is only as good as the population it ran over,
and ours did not reach the two things you changed most.

For the same reason we are not claiming Update 52 is otherwise sound. We
stopped after PR 96 deliberately.

## 3. A small request: name the release seed the same way twice

`seed_identity.py` on our side derives which Update a checkout is holding by
finding the release note that names the seed's hash. It refuses rather than
guesses, because an interim seed named in the next Update's accumulator would
otherwise get a release number it never earned.

Update 51 wrote:

    **Seed `C3181693` (2,917,073 bytes, SHA-256 ...

Update 52 writes:

    **The proofs, all at the release head against seed `61C81B04D0C3CC2E`:**

which is a sixth distinct spelling, in sixteen digits rather than eight. Our
deriver refused `u52` and would have banked Update 52 under its bare hash,
outside the rotation everything else references. We fixed it on our side and
the fix was slightly delicate, because Update 53's accumulator opens "through
its release head (main 20354, seed `61C81B04D0C3CC2E`)" -- the same two
phrases naming the same seed, one line apart in shape, so an over-broad rule
makes 52 and 53 both claim it.

**No change is needed for us.** But if a stable form is cheap -- one line per
release note that always reads the same way -- it removes a class of silent
mislabelling for anyone automating against the notes.

## What we are not reporting

PR 96 covers the duplicate `NoExpectTy` arms and the fact that Update 52
cannot be transpiled to zig without them. Nothing else in this Update stopped
a rung.

We are deliberately not hunting Update 52 further. Your agents follow this up
more holistically than we can from outside, and the ceremony above tells us
our population cannot see the parts that changed most.
