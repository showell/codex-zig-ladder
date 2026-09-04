# A hanging-indent prose continuation is lexed as CODE

**Status: HALF PROVEN. Do not send.** The lexer half is upstream's, read from
their source. The absorption half is measured only in our Rust interpreter and
needs the bare-metal oracle before anyone calls it a compiler defect.

## The rule, from upstream's own lexer

`Syntax/Lexer.codex`, `scan-token`: `skip-spaces` runs FIRST, and the prose test
is then `s.column == 2`. So the first non-space character must land at column 2
**exactly**. One leading space is prose and is skipped whole
(`skip-prose-line`). Three leading spaces is CODE.

A bullet whose continuation is aligned under its text therefore straddles the
line:

```
 - **Loudly.** `BuildScript.codex`, `vmconfigScript.codex` and      <- col 2, prose
   `comparecodexsemanticScript.codex` all refuse at 32 with ...     <- col 4, CODE
```

Upstream does this in at least `opening.codex`, `IR/IRCheck.codex` and
`Emit/X86_64Lir.codex`. Their lexer answers `ErrorToken` for the backticks
(`Lexer.codex:451` emits ErrorToken for any character its dispatch does not
know), and the parser then drops the tokens because they land in no construct.

**This is where a large part of `parsedump cover`'s "155,351 tokens landed in no
construct" comes from.** That number has been read past as noise.

## What we measured, and where

Their instances are benign BY LUCK: prose words and backticks cannot continue an
expression. Change the text and it is not benign. Measured with our interpreter:

    answer : Integer -> Integer
    answer (n) =
     n + 1

    A prose line at column 2 explaining the above, whose continuation
      + 1000

| continuation | `answer 1` |
|---|---|
| absent | 2 |
| at column 2 (proper prose) | 2 |
| **at column 4 (hanging indent)** | **1002** |

The column is the only variable.

## The question that decides who owns this

Upstream's `skip-prose-line` emits NO token, so their parser sees
`n + 1` `Newline` `Newline` `+ 1000`. Whether their parser continues a binary
expression across two newlines is not established here. Codex refuses multi-line
APPLICATIONS (CDX1070); this is a binary operator, which may differ.

- **If bare metal also answers 1002** -- a silent-miscompile hazard in the
  release, and this reproducer is the finding.
- **If bare metal answers 2** -- then the 1002 is OUR parser continuing an
  expression across skipped prose, and the finding is against us.

Run `ProseAbsorbRun.codex` through the bare-metal oracle and record which.
