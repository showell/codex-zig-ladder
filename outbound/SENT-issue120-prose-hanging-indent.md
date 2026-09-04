A prose line's hanging indent is lexed as CODE and joins the previous definition's expression, with no diagnostic.

## Reproducer

Three files differing in one thing: the indent of the continuation line.

```
Chapter: ProseCol4
  cites Foreword chapter Console

Section: Definitions

  answer : Integer -> Integer
  answer (n) =
   n + 1

 A prose line at column 2 explaining the above, whose continuation
   + 1000

Section: Entry

  opening : [Console] Nothing = act
   print-line-uni (integer-to-text (answer 1))
  end
```

| continuation line | `answer 1` prints |
|---|---|
| absent | 2 |
| at column 2 (` + 1000`) | 2 |
| **at column 4 (`   + 1000`)** | **1002** |

No diagnostic in any case. Measured on bare metal under QEMU with the Update 55
seed (81F9E817), compiled through the ring and run; a depot test with an
existing `.expected` (`ops/real-mode-opening`) was run first in the same rig and
reproduced its expected output byte-for-byte, so the rig is not the variable.

## Why

`Syntax/Lexer.codex`, `scan-token`: `skip-spaces` runs first and the prose test
is then `s.column == 2`. So a line is prose only when its first non-space
character lands at column 2 EXACTLY. At column 4 it is code.

`skip-prose-line` emits no token, so the parser sees

    n + 1   Newline   Newline   + 1000

and continues the binary expression across both newlines. Codex refuses
multi-line APPLICATIONS (CDX1070); a binary operator appears not to be refused
the same way.

## This is in the compiler's own source

A bullet whose continuation is aligned under its text straddles the rule:

    codex/compiler/opening.codex:114-117
    codex/compiler/IR/IRCheck.codex:38-39
    codex/compiler/Emit/X86_64Lir.codex:539

e.g. `opening.codex:115-116`

```
 - **Loudly.** `BuildScript.codex`, `vmconfigScript.codex` and      <- col 2, prose
   `comparecodexsemanticScript.codex` all refuse at 32 with ...     <- col 4, CODE
```

Those are benign, and only by luck: prose words and backticks cannot continue an
expression, so the tokens land in no construct and are dropped. (The backticks
do become `ErrorToken`s -- that is how we found this.) The same shape with
different words is a silently different program.

## What we are not claiming

We are not proposing that the column-2 rule change; it is deliberate and
everything else being code is what makes prose free-form. Nor have we surveyed
how often a hanging indent in the wild happens to form a valid continuation --
we found the mechanism, not a live miscompile in shipped code.

The part that looks wrong to us is the SILENCE. A line at column 3 or beyond
that immediately follows a prose line is far more likely to be a hanging indent
than code, and saying so costs nothing where guessing costs a wrong answer with
no diagnostic. A warning would also have flagged the three sites above.

Reported by Claude, working with Steve Howell. Reproducer and both controls:
`findings/prose-absorb/` in codex-zig-ladder.
