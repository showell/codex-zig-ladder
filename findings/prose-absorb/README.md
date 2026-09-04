# A hanging-indent prose continuation is lexed as CODE

**Status: SENT as issue 120, 2026-09-04.**
https://github.com/damiant3/Cobblestone/issues/120 -- `outbound/SENT-issue120-prose-hanging-indent.md` is the text as filed.

| | bare metal | our interpreter |
|---|---|---|
| `real-mode-opening` (depot control) | MATCHES its `.expected` | -- |
| continuation absent | 2 | 2 |
| continuation at column 2 | 2 | 2 |
| **continuation at column 4** | **1002** | **1002** |

The control is a depot test whose `.expected` is already the depot's, run FIRST
and reproduced byte-for-byte, so the rig is proven on the spot. Bare metal and
our interpreter agree exactly: OUR STACK IS FAITHFUL AND THIS IS UPSTREAM'S
DEFECT. Run with `bare_expected.py real-mode-opening prose-none prose-col2
prose-col4` against a u56-candidate checkout.

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

## Why it happens

`skip-prose-line` emits NO token, so the parser sees `n + 1` `Newline`
`Newline` `+ 1000` and continues the binary expression across both newlines.
Codex refuses multi-line APPLICATIONS (CDX1070); a binary operator is evidently
not refused the same way.

## What it costs, and what it does not

The three occurrences in the released compiler -- `opening.codex:114-117`,
`IR/IRCheck.codex:38-39`, `Emit/X86_64Lir.codex:539` -- are benign BY LUCK:
their continuation text is prose words and backticks, which cannot continue an
expression, so the tokens land in no construct and are dropped. Change the words
and the same shape is a silent wrong answer with no diagnostic anywhere.

A suggested fix is not ours to pick, but the cheap one is a diagnostic rather
than a semantic change: a line whose first non-space character sits at column 3
or beyond, immediately following a prose line, is far more likely to be a
hanging indent than code -- and saying so costs nothing where guessing does.
