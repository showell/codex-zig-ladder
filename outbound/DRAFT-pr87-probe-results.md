# Draft: PR 87 falsifier results, for the compiler lane

You asked for the outcome either way, including a null result. It is not
a null result. Not sent.

---

## The report

Three probes, run 2026-08-26 22:19 against our pin. Predictions were
written into each probe file before it was compiled, which is how we know
we got two of them wrong.

**The execution datum you wanted: arm B runs and answers correctly.**
We gave your arm B a base case so it terminates —

    gb : Integer -> (Integer -> Integer)
    gb (x) = if x <= 0 then (\y -> y) else gb (x - 1)

`(gb 3) 5` emits, builds and runs on the zig arm, answering `5`, matching
its `.expected`. `should-tco` fires on it, so the pass rewrote a
full-arity self tail call whose result is a closure, and the closure the
last frame built survived the rewrite. That is one executed arm rather
than a compiled one, as requested.

**The let-bound alias COMPILES. We predicted CDX2001 and were wrong.**

    fa : Integer, Integer -> Integer
    fa (x) (y) = let g = fa in g x

    codexir rc=0   diagnostics=NONE   halted=False

The `deck-record` variant compiles clean too, so it is not special to
`let`.

The wire shows why we think this is a hole rather than a shape we
misjudged. `fa` declares two parameters and its type peels to
`int-default` after two, and the body it accepted is

    (apply (name "g" ...) (name "x" int-default) (fn int-default int-default))

— type `(fn int-default int-default)`. A function where Integer was
declared. And the checker contradicts itself in the same IR: `opening`'s
call site is `(apply (apply (name "fa" ...) (int-lit 1) ...) (int-lit 2)
int-default)`, so it believes `fa 1 2` is an Integer while the body it
accepted makes `fa x y` a function. Both cannot hold.

Zig is the first component in the chain to object —
`expected 3 argument(s), found 2` — against an emitted
`fn fa(x: i64, y: i64) i64` whose body is `g.call(g.ctx, x)`.

**This does not reopen the row, and we are not asking you to.** Through
an alias the apply spine's root is `g`, not `fa`, so `is-self-call`
answers False and the gate still cannot fire. That half of our prediction
held. The row withdraws exactly as agreed.

What it does is answer Q1 differently in one corner. Your seven arms
established that the shape needs an infinite type and that the checker
refuses it — by name, via CDX2010, where inference is doing the work.
Through an alias the checker never asks: `g` gets a concrete type from
the `let`, `g x` gets a concrete function type, and nothing compares that
against the declared return type. The shape is still not well-typed. It
is accepted anyway.

**The two coverage corners: confirmed by reading, not a route.**
`has-tail-call` answers False for `IrTry` outright and `has-tail-call-act`
inspects only the last statement (`Emit/X86_64.codex:82-99`). Both are
real. Neither is a route to the shape — a tail call the pass declines to
optimise is a deeper stack, not a wrong answer — so we report them as
confirmed gaps in coverage and nothing more.

**One thing we could not measure.** The `deck-record` probe's zig verdict
is masked by a defect of ours: our prelude has a local named `fd`, our
probe named its function `fd`, and zig refused on the shadow before
reaching anything interesting. The compiler verdict — which is the actual
question — is clean and stands. We will re-run the zig half under a
different name.

---

## Notes for Steve before sending

- Two of three predictions wrong, said plainly and early. That is the
  part worth keeping.
- The finding is THEIRS and it is bigger than the row we withdrew, so
  the tone matters: we are handing back a result they asked for, not
  reopening an argument they closed.
- We are not claiming a reachable miscompile. We are claiming an
  unreported type error. Those are different and the draft says so.
