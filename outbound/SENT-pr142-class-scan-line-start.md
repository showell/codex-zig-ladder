# PR 142 -- Parser: a class or instance declaration begins its line (COMPILER-81)

https://github.com/damiant3/Cobblestone/pull/142  (sent 2026-09-12, branch
`class-scan-line-start` 33f50663 off clean Update 58 `5b3e14a7`)

`scan-class-instance-defs` walks the whole token stream; a section title's
words are tokens; so `instance <Type>` or `class <Type>` inside a title
declares a phantom instance or class, and two valid programs are refused
(CDX2006, CDX3001). Fix: the keyword must begin its line (`begins-line`).
Pinned by `codex/test/ops/section-title-keywords` (prints `<42>`); backlog
row COMPILER-81.

Found by rust-codex-compiler's counter gate: two ids short on
nrf52840-drivers, whose section title reads "shared with SPIM via instance
ID". Localized by widening a minimal unit one neighbour at a time (the
definition itself was exact in isolation).

Verified: the seed compiles the patched compiler source to IR under QEMU
(3m09s); the unpatched codexcheck at 8570fba1 refuses the pinning unit;
ours runs it to `<42>`; our diagnostics gate agrees with codexcheck on all
1,269 units with the same rule in place.

NOT verified, stated in the PR: a native codexir from the patched source
could not be built on this box. Two Update 58 plug gaps, both reproduced on
clean 5b3e14a7 (`~/showell_repos/cobblestone-u58clean` was cut for that and
removed after): `zigemit.zig:3892: local variable shadows declaration of
'cx_new'`, and `codexir.zig:18759: zig plug: no address-of for
codexir.IRActStmt` (and `IRPat`). Candidate findings for Job 2, offered in
the PR text, not yet filed. Logs: scratchpad `qemu-clean.log`,
`qemu-codexir2.log`.
