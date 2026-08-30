# Grading Math chapter Cordic

The measurement behind Cobblestone **PR 108**. Run 2026-08-30 against
`u53-rebank` (`58b08c38`).

**No box time is needed for the accuracy question.** `model.py` is a faithful
transcription of the chapter's own arithmetic -- truncating division included,
because Codex `/` truncates toward zero and Python `//` floors -- so the whole
domain can be swept in Python in a second.

    python3 -c "from model import sincos, true_sincos; print(sincos(300))"
    ./gen_test.py        # writes math-cordic-accuracy.codex from the model

## The result

    worst ABSOLUTE error  5.41 of 1000 full scale = 0.54%   at sin 3163
    worst RELATIVE error  3.68%                             at sin 3255
    docstring claims      ~0.1%, without saying which
    effective iterations  10 of 16 -- six atan-table entries are zero

## The model is validated twice, which is what makes it usable

**Against the depot's own committed expectations.** `math-cordic-quadrants.expected`
carries 18 cordic values Damian recorded; the model reproduces every one. Its
`true` column is also within half a unit of exact everywhere except `sin 2500`
(599 against 598.47) and `sin 3141` (0 against 0.59) -- sub-unit rounding
disagreements, not defects.

**Against bare metal.** The seed under QEMU was asked all 20 angles the new test
uses: zero disagreements with the model.

A model that had only matched one sampled value would not be worth trusting with
a docstring correction.

## The control failed, and reading why is the useful part

`math-cordic-quadrants` came back DIFFERS. Its committed `.expected` begins with
a stray `\x01` the program does not print; normalised, the two are byte-identical
across all 32 lines. **20 of the 398 `.expected` files under `codex/test/` start
with that byte and 378 do not**, so this is a format split in the depot rather
than anything about Cordic. Worth knowing before any future `.expected` is
settled here.

## The bound was shown to fire

`BOUND-PROBE.codex` is the test with its tolerance lowered from 6 to 2 and
nothing else changed. Bare metal answers `within 2 of 1000: 10 of 20` against the
test's `20 of 20`, so the counter is doing work rather than reporting a constant
(BOX Before-11).
