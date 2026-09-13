# Issue 146 -- a nullary constructor of a polymorphic sum leaves its parameter unbound in typed IR

https://github.com/damiant3/Cobblestone/issues/146  (sent 2026-09-13, against
clean Update 60 `9fff850c`, seed `CF9EDD812EA7E78B`)

An issue rather than a PR: it is an IR comparison with no fix to propose, since
upstream's COMPILER-81 row asks them to decide finalization policy for unbound
variables ("do not silently default types inside a plug").

Found by curated-tests `run-zig` on `roc-poly-nopayload-variant`, the one roc
refusal left at U60 that no upstream row named.

## The reproducer sent

    Foo (a) = | Bar (a) | Baz
    inspect-foo : Foo a -> Text
    inspect-foo (ignored) = "ok"
    opening prints (inspect-foo Baz) then (inspect-foo (Bar 1))

    seed on bare metal (assemble_unit.ps1 + ring_compile.py):
        (name "Baz" (ctd "Foo" (args (tvar 287)))), no .diags written
    native codexir (~/codexir 5aa4b516):  (tvar 7) at the same site
    codexzig (~/codexzig 8169dac4) -> zig 0.16.0:
        error: zig plug: type variable T7 is not declared at this site

Controls: Bar 1 + Bar 2 builds (ok ok); Baz twice is refused; a lone `Baz`
call builds because the emitted `opening` is `(text-lit "ok")`, with the call
gone; a lone `Bar 1` call builds and keeps the call.

## The cold read changed the draft

A subagent read the first draft cold against the evidence files, and it caught
three problems:

- "whether it is refused depends on how many callers" was contradicted by the
  single-caller `Bar 1` control, which keeps its call. The issue now says only
  what the IR shows, and that we do not know which pass removes the lone `Baz`.
- Three claims had no evidence in hand: the T287 number for a unit carrying
  ListUtils/Tuple (that was the roc unit), the wasm plug's result (the roc unit
  only), and "no diagnostics". The first two were cut. The third is supported:
  ring_compile.py writes `<out>.diags` whenever the seed reports anything, and
  none was written.
- The Rust front end's `int-default` sentence was cut, because it reads as the
  very default COMPILER-81 warns against.

Evidence was in the session scratchpad `u60/t287/` and is not kept.
