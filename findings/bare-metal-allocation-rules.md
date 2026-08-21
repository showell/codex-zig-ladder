# Bare metal's allocation rules, and a shadow counter that applies them

Derived from the x86-64 builtins and then **validated against a running
bare-metal binary**, 2026-08-21, using `findings/probe-memory-model.codex`.
Written down because the zig arm's deck guard currently answers the wrong
question, and this is what it needs in order to answer the right one.

## The rules

| operation | bare metal charges | source |
|---|---|---|
| `__list-with-capacity c` | `16 + c*8` | `emit-list-with-capacity-builtin-bivy`, `Emit/X86_64Builtins.codex:1058` |
| list literal of n | `16 + n*8` | `emit-list-bivy`, `Emit/X86_64Compound.codex:2160` |
| `&` over k operands, t elements | `k*8 + 16 + t*8` | `emit-concat-many` → `__list_concat_many`, `Emit/X86_64.codex:2312`, `X86_64ListHelpers.codex:814` |
| `::` onto a list of n | `16 + max(2*(n+1), 4)*8` | `__list_cons`, `X86_64ListHelpers.codex:66` |
| snoc / `list-push` | extends in place when its block is on top, else a fresh block | `__list_snoc`, `X86_64ListHelpers.codex:245,288` |
| text of len | `8 + align8(len)` | `emit-str-concat-slow-alloc`, `Emit/X86_64TextHelpers.codex:223` |
| text append to an accumulator | the appended bytes only | `__str_concat_inplace`, `X86_64TextHelpers.codex:287` |

An element is **8 bytes whatever its type** — a `List Text` costs the same
as a `List Integer`, because a text is one word. That is the whole of
finding 21's 3,145,824: our `Text` is a 16-byte zig slice.

## The validation

A shadow counter applying these rules, run against the probe's own meters,
versus what the bare-metal binary actually spent:

    meter                bare metal              shadow
    list literal 1/2/4/8 24 / 32 / 48 / 80       same
    capacity 0/16/256    16 / 144 / 2064         same
    concat 4 & 4         192                     same
    text concat 2        16                      same
    List Integer/Text 4  48 / 48                 same
    cat-accum            20240 73232 277520      same
    push-accum           528 1040 2064           544 1040 2064
    text-accum           72 136 264              79 143 271
    chain a&b&c&d        176                     264

Eleven of fourteen exact, including a three-point quadratic series to the
byte. Two carry a small first-allocation bias: the model sums per-operation
increments where bare metal pays alignment once on the finished block, so an
accumulator's opening block is over-charged by 8-16 bytes. It is a constant,
it does not grow with n, and it is not worth chasing.

## The one real mismatch, and why it is the point

`chain a&b&c&d` costs bare metal 176 and the model 264, because **bare metal
flattens the chain** (`flatten-append-chain`, `Emit/X86_64.codex:2284`) into a
single `__list_concat_many` sized at the true total, while ZigEmitter emits
pairwise `cx_ll_concat` and materialises every prefix. An n-chain is Θ(n²)
elements here against n on bare metal.

That is a divergence the shadow counter cannot paper over and should not: it
prices the operations we actually perform. Where the number disagrees with
bare metal, either the model is wrong or the emitter is -- and here it is the
emitter. `ast/fibx.zig` has 205 nested `cx_ll_concat(cx_ll_concat(` sites and
293 nested `cx_concat`.

## Why this matters more than the number it produces

The deck guard added in `62ee2dd2` refuses when the zig arm's allocation
overruns bare metal's reservation. But the two arms allocate differently by
design, so that check answers "does zig's differently-shaped allocation fit
bare metal's budget" -- not "would bare metal overrun". It false-alarmed for
an entire investigation. Metering bare metal's rule separately, and refusing
on **that**, restores the question the ladder exists to ask, and turns the
gap between the two counters into a standing measure of how faithful the
plug's allocator is.
