# reference/ -- other people's code, kept here to CRIB FROM

**Nothing in this directory is ours, nothing here is built, and nothing here
is run.** It is third-party source vendored verbatim so that a port can be
checked against what it was ported FROM without a network round trip and
without drift.

If you are looking for code this project compiles, you are in the wrong
directory: the ladder's own sources are at the repo root, the probes are in
`findings/`, and the ported tests live in the DEPOT (`codex/test/`), not here.

## Why vendor at all

The Roc ports in `codex/test/roc-*.codex` exist because their expected values
were written by people who never heard of Codex. That is the one property our
own probes can never have -- a probe tests what we already suspect. The
property only holds while each port can be checked against the original case,
so the original has to be readable, pinned, and unedited.

A port that cannot be traced back to its source is just a program we wrote.

## What is here

    roc-lang/eval_closure_recursion_tests.zig
        roc-lang/roc, src/eval/test/eval_closure_recursion_tests.zig
        pinned at commit ade9294db807e9f3e0c4b3b8d945cd19a477ee1b (2026-06-18)
        sha256 322ab657d31b3a302a384c090d3e24f94bcaaa2fd5c8f2375f9de9ffddd4ee77
        1372 lines, 117 test cases, verbatim and unmodified

    roc-lang/LICENSE
        the Universal Permissive License v1.0 it is distributed under, and
        the copyright notice the licence requires be carried with it:
        Copyright (c) 2019 Richard Feldman and subsequent Roc authors
        <roc-lang.org/authors>

All eleven `roc-*` ports in the depot come from that one file.

## The rules

- **Verbatim.** Never edit a file here to make a port easier. If the port
  needs an adaptation, the adaptation belongs in the port's own prose, where
  it is visible and argued -- every existing port names its adaptations.
- **Pinned.** A file here records the commit it was taken at. Re-taking it is
  a deliberate act with its own commit, not a refresh.
- **Not built.** No ladder script reads this directory. It is for humans and
  for checking a port's fidelity.
