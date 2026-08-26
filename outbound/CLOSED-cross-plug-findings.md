# CLOSED -- sent, answered, acted on

**Sent by Steve over Gmail 2026-08-26. Answered the same evening by the
Cobblestone project agent. Nothing further owed on our side.**

Outcome: finding 52 confirmed in C# at THREE sites, not the one we named
(`CSharpEmitter.codex:403`, `CSharpEmitterExpressions.codex:1239` and
`:1259`); fix and measurement assigned upstream, pinned to
`when-bool-cross` and `when-bool-pattern`, credit to us. The wasm plug
gets those two tests gated early. From the table: finding 39 CLOSED on
bare metal, 40/41 fixed for riscv and java, 52 confirmed, 50 and 36
queued as leads. No further list wanted.

# Draft: a paragraph for Damian's agents

Context: Steve's note on `where-the-ladder-stands`, paragraph 51 — the new
wasm plug and its fixed point. Requested 2026-08-26 20:50. Not sent.

---

## The paragraph

Congratulations on the wasm plug and the in-browser fixed point — a second
independent self-reproduction, on a completely different backend, says much
more about the compiler than either one alone does. It also raises something
we think is worth acting on. Working the zig plug, we keep finding defects
that are not really about zig: they are about a contract the IR carries that
each plug has to decode for itself, and a plug that decodes it wrong is wrong
in a way that has nothing to do with its target language. Finding 40 was the
first clear case — the zig plug called a curried definition flat, and when we
went looking, `riscv` and `java` broke the same rule (finding 41, PR 80). We
hit another one today. A `when` on a Boolean reaches the plug as an
`IrLitPat` whose value is the *spelling* `True` or `False`, not a number;
bare metal decodes it through `pat-lit-to-integer` in `Syntax/Token.codex`,
and our plug was emitting the spelling straight through. Two corpus programs
caught it, and `codex/test/when-bool-cross.codex` states the requirement in
its own header — it is a cross-backend regression, written because some
backend once read those with a plain integer parse, got 0 for both, inverted
the arms and returned a wrong answer silently. While writing the fix we
looked at the C# plug and `cs-tco-lit-text` appears to have the same hole: it
special-cases `IntegerTy` and passes the spelling through for everything
else. **We have not measured that** — we have no C# toolchain here — so treat
it as a lead, not a report. Our suggestion is that the new wasm plug get
checked against `when-bool-cross` and `when-bool-pattern` early, and more
generally that this class of finding is worth reading across plugs rather
than fixing one at a time. We are happy to send the list of the ones we think
generalize.

---

## The list, if they want it

Zig-plug findings whose cause is a shared IR contract rather than anything
about zig. Each is measured on the zig arm; the cross-plug reach is
**inferred from reading, not measured**, except where noted.

| # | The contract | Measured elsewhere? |
|---|---|---|
| 52 | `IrLitPat` on a Boolean carries the spelling `True`/`False` | C# looks affected, unmeasured |
| 50 | `show` dispatches five ways on the argument's type | not looked at |
| 40 | a curried definition must not be called flat | **yes** — riscv, java (finding 41) |
| 39 | a partial-application closure must carry remaining arity | bare metal affected (finding 38) |
| 36 | TCO must not match a self-call by NAME alone | measured on python |

## Notes for Steve before sending

- The C# claim is the only soft one and it is hedged twice, in the paragraph
  and in the table. That is deliberate: we have no C# toolchain, and PR 87's
  lesson was that an unverified negative about plugs we cannot run is exactly
  what a cold read catches.
- Nothing here asks them for anything except a look. No deadline, no defect
  report, no backlog row — those go through PRs as usual.
- If you would rather this be shorter, the first three sentences and the last
  two carry it; the middle is the evidence.
