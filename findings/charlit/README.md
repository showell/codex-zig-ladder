# `scan-char-literal` never diagnoses an unterminated character literal

**Status: read from source at U54, NOT yet run.** The repro beside this note
has not been compiled on either arm. Everything below is a reading of
`codex/compiler/Syntax/Lexer.codex` at `14ec571b`.

## Where it came from

Upstream found it while verifying our PR 114 and said so in the review:

> One correction to the row you contributed, verified at head: the four sibling
> scanners are safe as you say, but `scan-char-literal` has no unterminated
> diagnostic at all. A quote followed by a newline consumes the newline as the
> character, finds no closing quote, and emits a CharLiteral without complaint.
> Same family, different shape, still open.

So the row we wrote for COMPILER-35 read the lexer as clean and it is not.

## It is wider than the newline case they described

`scan-char-literal` has three exits and checks for the closing quote at exactly
one point, conditionally, in each of the two non-empty paths:

    in let s3 = if is-at-end s2 then s2
                else if peek-code s2 == cc-single-quote then advance-char s2
                else s2
    in LexToken (make-token (deck-record CharLiteral) (s3.offset - s.offset) s) s3

The `else s2` arm is the defect. When the byte after the character is not a
closing quote, the scanner does not consume it, does not complain, and emits a
**CharLiteral anyway**. Nothing downstream can tell that token from a
well-formed one.

END OF INPUT IS CAUGHT and end of line is not, which is the same asymmetry
COMPILER-35 was about one literal kind over:

| input | what happens | loud? |
|---|---|---|
| `'` at EOF | `is-at-end s1` -> ErrorToken | yes |
| `'\` at EOF | `is-at-end s2` -> ErrorToken | yes |
| `'a` then newline | CharLiteral, length 2 | **no** |
| `'` then newline | the NEWLINE becomes the character | **no** |
| `'ab'` | CharLiteral over `'a`, then `b`, then a stray `'` | **no** |

The third and fifth rows are not in upstream's description. The fifth is the
nastiest: a two-character literal silently becomes three tokens, and the stray
quote then opens a NEW char literal that swallows whatever follows it.

## Why the text path is loud and this one is not

`scan-string-end` stops on `cc-newline`, and `scan-string-body` then asks
whether the byte before the stop was the closing quote -- so end of line falls
into the `terminated == False` arm and raises `cdx-unterminated-text`. That is
the shape PR 114 repaired.

`scan-char-literal` has no equivalent question. It never compares the stop
against a terminator; it just optionally advances past one.

## The fix shape

Mirror `scan-string-body`: bind whether the closing quote was actually there,
and raise on the negative. There is already a diagnostic code for the text
case (`cdx-unterminated-text`); whether a character literal deserves its own
code is a call for whoever takes it, and the message should differ because the
advice differs -- a text literal wants a closing `"` on the same line, a
character literal wants exactly one character and a closing `'`.

## What this note is missing

A measurement. `charlit-probe.codex` beside this file is the repro; it has not
been compiled on bare metal or through any plug, and until it has, the table
above is a reading rather than a result. The rows that matter most are the
ones the table calls silent -- a silent row is only a finding once something
has shown it produces a CharLiteral and no diagnostic.
