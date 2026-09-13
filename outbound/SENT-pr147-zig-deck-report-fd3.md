Title: zig plug: the deck report goes to fd 3, and only when fd 3 is open
URL: https://github.com/damiant3/Cobblestone/pull/147

Branch: showell/NewRepository `zig-deck-report-fd3`, two commits on Update 60 (`9fff850c`)

---

**What changes.** `cx_deck_report` writes `CX-DECK used=... reserved=... headroom=... base=... peak=... best=...`; it came in with PRs 77, 81 and 83 (landed in `111c0fea`). It wrote to fd 1. It now writes to fd 3, and only when fd 3 was open at the program's first `cx_deck_set`; otherwise it writes nothing. `codexir < prog.codex 2> prog.ir 3> deck.log` asks for the measurement.

- A new prelude part, `cx_deck_fd`: a `zig-p-` fragment list, a `ShakePart` row and a `zig-prelude-decls` entry. It is 3 when fd 3 was open, -1 when not, and -2 until asked.
- `cx_deck_set` asks `fcntl(3, F_GETFD)` once, inside an `os.tag == .linux` guard.
- `cx_deck_report` returns unless `cx_deck_fd` is 3, then writes there.
- The part-count prose above the masks reads 111. It read 100, with 110 parts in the table.

**Why.** The compilers this plug builds use fd 1 for their own notices. `codexzig` writes its non-error diagnostics there. Our IR harness for `codexir`, which lives in our transpiler repository and not in this tree, writes its warnings there through `write-binary`. A reader of those notices has had to set the telemetry aside first. On our side:

- `build_codexir.py` echoes codexzig's stdout while it transpiles each of its two oracles, and the echo carried 410 `CX-DECK` lines per oracle, with the verdict lines among them;
- at Update 57, the wasm transpiler's diagnostics file held 396 lines from the native road and 3 from the wasm road, so it was moved out of git;
- a comparison of our interpreter against `codexir` read 36 of 54 units as different when only these lines differed.

Nothing in the tree reads `CX-DECK`: it appears only in `ZigEmitter.codex`.

**Why the question is asked at the first `cx_deck_set`.** The prelude opens a file in one place, `cx_read_file_uni`, and closes it before returning. So at that moment an open fd 3 was inherited, and while it stays open nothing the program opens is numbered 3.

**What the probe does not know.** It tells whether fd 3 is open, not why. A process that inherits fd 3 for another purpose, such as a make jobserver or systemd socket activation, receives the lines there.

**What a program without a deck sees.** A program whose prelude reaches `cx_deck_report` without `cx_deck_set` gains the variable, one early return and the new write argument. `arith.codex` is one. It never reported before, because its `cx_deck_base` stays 0, and it does not now.

**Verified** on Linux with zig 0.16.0, against Update 60, at the branch's first commit (`55760826`). The second commit changes two prelude comments and the count prose, no zig code, and was not rebuilt.

1. **The deck parts alone.** The parts, compiled into a program that arms a deck and asks for a report:

       Update 60   fd 3 closed or open   the CX-DECK line on stdout
       candidate   fd 3 closed           nothing on stdout, stderr or fd 3
       candidate   fd 3 open             the CX-DECK line on fd 3, stdout empty

2. **A scratch fixed point on the candidate.** Four steps:
   - under QEMU, the seed compiles the ring plug and the transpiler;
   - still in the guest, the ring plug transpiles the transpiler;
   - zig builds that output;
   - the native binary transpiles the same source again.

   Its zig is byte-identical to the guest's, in 475 s, and `arith.codex` matches all 9 expected lines. Against Update 60's, the transpiler's emitted zig differs in 37 lines (10 removed, 27 added): the three parts above, and the transpiler's own copies of those fragments, of `zig-prelude-decls` and of the part table.

3. **`codexir` built from the candidate, against Update 60's `codexir`,** over 128 units (28 cut from `codex/test`, 46 Roc ports, 54 of our safari specs):
   - IR byte-identical, notices identical, and no `CX-DECK` line on stdout;
   - with fd 3 open, the candidate writes there the same `CX-DECK` lines, by count and `used=` value, that Update 60 wrote to stdout; 36 units write a report.

4. **`codexrun`, the interpreter in our Rust Codex compiler,** running `codexir-subject.codex` on each of the 54 safari units, matches the candidate `codexir` byte for byte with nothing set aside. At Update 60 it had to set aside `CX-DECK` lines on 36 of them.

**Not verified.**
- `build/check-zig-prelude-surface.ps1`, which its own header asks for after a prelude change: its compile path is out of reach here. The emitted surface gains one name, `cx_deck_fd`, declared in `zig-prelude-decls`.
- Windows: the report was Linux-only before and stays so, and the probe sits inside the same guard.

No backlog row: nothing is left open.

Written by Claude (Anthropic) working with Steve Howell.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
