# PR 154 -- two refusal tests for issue 153

https://github.com/damiant3/Cobblestone/pull/154  (sent 2026-09-22, branch `empty-list-literal-tests` `b1427d98` off Update 61 `3af67f99`, worktree `cobblestone-emptylist`)

Damian asked that bugs like #153 arrive as a test in the BVT or language battery. Red at U61 by design. The code (2001) is what the seed reports for [1] in the same positions; both test files compile clean on the U61 seed. Backlog row COMPILER-85.

## The body sent

Two refusal tests for #153, as asked, and a backlog row for the gap.

**These tests are red at Update 61 by design.** They pass when the checker stops accepting `[]` as a non-list; nothing in this PR changes the compiler.

| test | source | `.failing` |
|---|---|---|
| `codex/test/errors/empty-list-as-integer` | `opening : Integer = []` | `2001` |
| `codex/test/errors/empty-list-as-text` | `opening : Integer = text-length []` | `2001` |

## Why 2001

The same two programs with `[1]` in place of `[]` are refused with exactly CDX2001 and nothing else. Measured on the Update 61 seed (`3af67f99`, `7BCD5BC6BCE0AF41`) on bare metal (QEMU), mode `IR-CCE`, with the unit `build/compile.ps1` would assemble:

| `opening : Integer =` | diagnostics |
|---|---|
| `[1]` | CDX2001 |
| `[]` | none |
| `text-length [1]` | CDX2001 |
| `text-length []` | none |

The two test files in this branch were compiled the same way and both compile clean today, so both will fail in the battery until the fix. If the eventual repair reports a different or an additional code, the sidecars are the thing to change; the claim they carry is only that these programs must be refused.

## The backlog row

COMPILER-85, at the top of the table in `codex/compiler/compiler-backlog.md`. It names the site (`infer-list`), the two tests, and #153. Renumber it if 85 is taken on your side.

Not included: the nested shape from #153 (`[[]]` carrying `error` in a clean compile) and the `MkTup2` typing in the issue's comment. Neither is a refusal, so neither fits `errors/`; `build/ir-fidelity` looks like their home, and we have not run it here.

---
Written by Claude (Anthropic's model) with Steve Howell.
