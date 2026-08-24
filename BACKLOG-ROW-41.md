# Outbound: the backlog row for finding 41

TEMPORARY -- delete in the commit that records it as sent, the way
PR-HEAP-UNIFICATION.md was and BACKLOG-ROW-37.md will be. Until then
this is the draft of the only route this finding has upstream
(contrib/README.md: a small branch off master with a `Ladder:` line,
entry in the quire's backlog).

This one goes to `codex/plugs/plugs-backlog.md`, not the compiler
backlog: every site is a plug. **Next free number is 1.57** (the file's
open entries run to 1.56).

Doc-only, and unusually well-founded for a doc-only row: the rule it
reports against is upstream's own, already written at
`docs/DevelopersRulebook.md:256-260`, in the section addressed to plug
authors. The row reports non-compliance with a stated contract rather
than proposing a design, which is the strongest shape a report like this
can take.

**Be exact about the citation.** The rule is the bullet at `:256-260`
and it is unqualified -- it binds "a plug", and names the TS/JS family
only as plugs that ALREADY carry the model. The plug list at `:254`
(`arm64`, `riscv`, `zig`, `t3isa`, `pascal`, `python`) belongs to the
neighbouring LAMBDA bullet and must not be quoted as though it scoped
this rule. An earlier draft conflated the two; upstream will check.

**One rule, four places, and only one of them observed running.** The
zig site is finding 40 and is OURS to fix -- item 3's queue carries it,
and it is the only one with an end-to-end reproducer. Finding 36 (the
python plug's TCO keying on name rather than arity) is the same rule
broken at a different stage and is filed separately at MEDIUM
confidence. This row is the riscv and java half, found by reading the
family while settling finding 40.

**The limitation is stated in the row itself, deliberately.** The
backlog's own standing hazard says a name census cannot answer a
semantics question and that the way to settle one is to run a subject
through the plug and read the output. That was done for zig. It was NOT
done for riscv or java: this box has no PowerShell and no prebuilt plug
binaries, so `build/run-plug.ps1` and `test-plugs.ps1` cannot run here
at all -- the same toolchain wall entry 1.20 records for Free Pascal.
What is offered is therefore the dispatch code and a grep anyone can
rerun in seconds, not an observed miscompile. Saying so is the point;
PR 78 was closed unmerged for claiming more than it had measured.

---

| 1.57 | **`riscv` and `java` break the curried-application rule in `DevelopersRulebook.md:256-260`, and riscv's correct over-apply is already in the tree, never called** | From the zig-plug ladder, 2026-08-24 (`findings/README.md` 41; the zig sibling is 40). The rulebook requires three cases of a plug that knows the callee's arity -- flat at that arity, under-applied with one arrow per missing parameter, **over-applied by applying the rest** -- in the section headed "What the wire carries, for anyone writing a plug" (`:243`). The rule is unqualified: it binds "a plug", with no list narrowing it, and names the TS/JS family only as plugs that already carry the model. Three plugs implement two of the three. **`riscv` has the fix and does not call it:** the named-definition path (`RiscVCodeGen2.codex:583-591`) tests `list-length args < known-arity` and routes to `rv-emit-partial-application`; every other case, `args > known-arity` included, falls into `rv-emit-direct-call` with the whole argument list. Seventy lines below, `rv-emit-closure-over-apply` (`:660-668`) is a correct take/drop over-apply, and `grep -rn rv-emit-closure-over-apply codex/plugs/` returns exactly three hits -- its signature, its definition, and its own self-recursive tail. Nothing reaches it. **`java` never consults arity at all:** `JavaEmitter.codex:158-168` emits `func & "(" & emit-jv-apply-args args ... & ")"` for both the `IrName` root and the `otherwise` root, and `lookup-arity`, defined at `:69-70`, has no call site in the file. **`arm64` is a near miss rather than a defect:** it has `a64-emit-oversaturated-call` (`Arm64CodeGen2.codex:927-932`) reached from `:980-981`, but the arity it consults is `a64-known-arity` (`:901-915`), a hardcoded table of builtin names, so it does not fire for user definitions; its local-closure path (`:976-978`) does use a real def-arity table. For contrast, the plugs that comply do it two ways: `csharp` (`CSharpEmitterExpressions.codex:830-841`), `python` (`PythonEmitter.codex:646-655`), `javascript` (`:501-511`) and `rust` (`RustEmitter.codex:547-560`) route every non-exact case to a curried spine so over-application is correct by construction, while the TS family (`TypeScriptEmitter.codex:205-214` plus angular, electron, react, svelte, vue) splits on `args > ar` explicitly with take/drop -- as does the compiler's own x86-64 back end at `X86_64Compound.codex:154`, from an arity map built at `:38` from `list-length (d.params)`. **What is measured and what is not:** the same defect in the zig plug is observed end to end -- `((even-fn 4) 20) 22` against a one-ary definition emits `even_fn(4, 20, 22)` and zig refuses it at compile time with `expected 1 argument(s), found 3` (ladder `findings/prim-closure.codex`). For riscv and java this row offers the dispatch code and the grep, NOT an observed miscompile: no PowerShell or prebuilt plug binary exists on the ladder's host, so `test-plugs.ps1` cannot run there, and nothing in the harness compiles emitted Java in any case. Treat the runtime consequence as inferred from the emitted shape. **Why none of it was caught, which may be the more useful half:** `codex/plugs/test-input/partial.codex` exercises under-application, saturation, and over-application of a LOCAL, but never over-application of a named top-level definition -- the one shape all three plugs mishandle -- and `codex/plugs/test-plugs.ps1` judges exit code, non-empty output and text markers (`:93-97`, `:163-177`) without ever compiling what it emitted. A single added definition in `partial.codex` would put all of these in front of a compiler. **The ask is one ruling:** whether over-application of a named definition is required of every plug that keeps an arity map (in which case riscv wants its dead function wired up and java wants an arity check), or whether some plugs are exempt and the rulebook's line 258 should say which. |

---

## The PR body

Off `upstream/master` (`5b8091e2` at the time of writing; rebase before
sending). Doc-only: one row added to `codex/plugs/plugs-backlog.md`,
nothing else in the diff.

    Plugs backlog: riscv and java do not handle over-application

    codex/plugs/plugs-backlog.md gains entry 1.57.

    DevelopersRulebook.md:256-260 requires a plug that knows the callee's
    arity to handle three cases -- flat, under-applied, over-applied.
    The rule is unqualified and binds any plug keeping an arity map.
    riscv and java implement two of the three. riscv's named-def path falls through
    to a flat direct call when args > arity, while a correct take/drop
    over-apply sits at RiscVCodeGen2.codex:660-668 with no caller. java
    never consults arity on either apply path and its lookup-arity is
    dead code.

    The zig plug has the same gap; that one is observed end to end and is
    ours to fix, so it is not in this row.

    The runtime consequence for riscv and java is inferred from the
    dispatch code, not observed: the ladder's host has no PowerShell and
    no prebuilt plug binaries, so the plug harness cannot run there. The
    row says so.

    Also noted, and possibly the cheaper fix: plugs/test-input/partial.codex
    covers over-application of a local but never of a named top-level
    definition, and test-plugs.ps1 never compiles what it emitted.

    Ladder: curried-apply

**Before sending, confirm:** the row number is still free (the file is
edited upstream), `upstream/master` is current, and the ladder tag
`curried-apply` is pushed and reachable.
