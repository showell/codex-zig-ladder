# The recursive structural-eq helper is synthesised below the IR, so it reaches one backend

*Draft. Written by Claude, on Steve Howell's account and at his direction.
Supersedes an earlier draft of this file that had the cause wrong; a cold read
caught it before sending.*

---

## The claim

Codex has two structural-equality mechanisms and they sit on opposite sides of
the IR. One reaches every backend. The other reaches exactly one.

- **`deriving Eq`** synthesises a source-level `__eq_<T>` in the desugarer
  (`Ast/Desugarer.codex:663`, `:765-777`), and `lower-eq-dispatch`
  (`IR/Lowering.codex:646-656`) rewrites `==` into a call to it **in the IR**.
  Above the wire, so every plug in the fleet inherits it for free.
- **The recursive-sum helper** is synthesised in the back end
  (`Emit/X86_64.codex:2911`, `:3062`, `:3257-3271`, appended by
  `X86_64Chapter.codex:1150`). **Below the wire.** `grep -rl
  "eq-sum-is-recursive\|__eq_" codex/plugs/` returns nothing.

**You already know the consequence for one backend.**
`codex/test/recursive-eq.no-cross` reads:

> structural == on a recursive variant is synthesised by the x86-64 emitter
> only (COMPILER-24); arm64 answers ne where eq is expected, riscv unmeasured

**The ask: hoist the recursive synthesis into lowering, where `deriving Eq`
already lives.** That fixes arm64, riscv and the zig plug in one place, at the
level where the other mechanism already works.

## What we measured, and it is only a third witness

`findings/probe-recursive-eq.codex` in our tier set, both arms:

    row                          bare metal   zig plug
    equal shape, two objects     yes          no      <-- disagrees
    different shape              no           no
    a value compared to itself   yes          yes
    equal shape, nested          yes          no      <-- disagrees
    different shape, nested      no           no

`Tree = | Leaf (Integer) | Fork (Tree) (Tree)`, values built through functions
so neither arm can fold two constructions into one object. `__eq_Tree` appears
exactly once in the bare-metal CDX map. The zig arm emits `(a_ == b_)` — the
`IrEq` arm at `ZigEmitter.codex:1303` special-cases Text and otherwise emits a
raw `==`, and a self-recursive sum is a pointer in that plug, so `==` is
identity.

The two agreeing rows are the diagnosis rather than noise: a pointer comparison
gets "different shape" and "a value compared to itself" right, so a probe with
only equal-shape rows could not have told identity from a broken structural
compare.

**This adds arm64's `ne` and zig's silent `no` to the same cause.** It is your
own note that establishes the pattern; we are the second data point, not the
discoverer.

## What is NOT wrong, so the report is not read as bigger than it is

We checked, and these all agree:

| sum shape | zig type | zig `==` | bare metal | verdict |
|---|---|---|---|---|
| generic (`tparams > 0`) | `union(enum)` | compile error | structural | loud |
| all-nullary | `enum` | correct tag compare | `emit-sum-tag-eq` | **agree** |
| self-recursive | pointer | identity | `__eq_<Sum>` | **this issue** |
| non-recursive + payload | `union(enum)` | compile error | `emit-sum-full-eq` | loud |

And a plain record without `deriving Eq` is compared by pointer on **both**
arms — `emit-eq-op` falls through to `emit-comparison`
(`X86_64.codex:2927`, `:3300-3308`), which your source says is deliberate:
*"It answers True for records, lists and sums on purpose… compares those by
POINTER and means to."*

So there is exactly one silent divergence, not a family. An earlier draft of
this issue claimed otherwise and we cut it.

## What our ladder could not see this Update, stated so our quiet is not read as a clean bill

Across the twelve compiler-chapter subjects our rungs compile: **zero `__eq_`
symbols** in any subject's CDX map, so this path never fired anywhere in our
population; and **no CDX2052 diagnostics** (an existing code that Update 52
gave a new message under, `Types/TypeCheckerInference.codex:562-564`).

Our fourteen truths came back byte-identical to the Update 51 bank. The honest
reading is not "Update 52 changed nothing" — it is that our population does not
reach the parts that changed. We also did not have a green DDC at Update 52's
release commit: six of twelve units could not be transpiled at all until the
duplicate `NoExpectTy` arms were removed, which your change 20398 had already
done at head. With that in, we now sweep **14/14 both arms**.

## One small request

`GitHubUpdate52.md` publishes no SHA-256 for its seed. Updates 48–51 each gave
the full 64-hex digest, and our side derives which Update a checkout holds by
matching the seed's hash against the release note that names it — refusing
rather than guessing, so an interim seed cannot inherit a release number. With
no digest published, that derivation had nothing to match and refused Update 52.

**One line per note carrying the full digest** would remove a class of silent
mislabelling for anyone automating against the notes. Nothing else needed.

## What we are not reporting

We are not hunting Update 52 further; your agents cover it more holistically
than we can from outside, and the section above says why our population is a
weak instrument for it.

Closing the zig side of the recursive helper is ours to do, and we expect to.
The fix-location argument is worth more than our half of it, which is why this
is an issue rather than a patch.
