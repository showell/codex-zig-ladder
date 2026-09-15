Title: Fireworks: rnd wraps, as the hash beside it does
URL: https://github.com/damiant3/Cobblestone/pull/151

Branch: showell/NewRepository `fireworks-rnd-wraps` (`c59e3686`), one commit on
Update 60 (`9fff850c`); worktree `cobblestone-fireworks`. The earlier branch
`fireworks-rnd-wrapping` (`835dea9e`) holds the same tree under a commit
message that named the wrong first trap; it is pushed and unused.

How it was found: roc-apps' framebuffer platform stopped Update 60's Fireworks
with `Integer multiplication overflowed` before its first flush.

The description was read cold by a fresh agent given the repositories. It
found the in-range claim wrong (only inputs -1 to 17 stay in range), the
Python missing 207360, the promised probe absent, and better citations:
DevelopersGuide's left-operand rule, the IR's `mul-int-wrapping`, plugs-backlog
2.21's probe convention, the history and the web app's precedent. All
addressed; it also ran the patched app's whole 3,900-flush cycle. The send is
the text below.

---

*Written by Claude (Anthropic), working with Steve Howell, on his account and at his direction.*

**What changes.** One commit on Update 60 (`9fff850c`), in `apps/fireworks/Fireworks.codex`:

- **`cites Foreword chapter Wrap64`.**
- **`rnd`'s parameter** becomes `Integer between -9223372036854775808 and 9223372036854775807 wrapping`, the type `hsh` in the same chapter already declares.
  - Its first line, `n * 374761393 + 668265263`, then wraps.
  - The IR spells it `add-int-wrapping (mul-int-wrapping (name "n" …) …)`.
- **`rnd`'s second multiply** becomes `w64-mul b 1274126177`, which the IR spells `mul-int-wrapping (name "b" int-default) (int-lit 1274126177)`.
  - The parameter alone does not reach it. `b` is `bit-xor`'s result, and `docs/DevelopersGuide.md` gives the rule: "A literal or a builtin result on the left is trapping whatever the inputs were declared, which is why the mixers route a bit-op result through `Foreword chapter Wrap64`'s `w64-mul`".
  - `FireworksShow.codex` multiplies by the same constant through `w64-mul`.

**Why.** Since COMPILER-36 (Update 55) a plain `Integer` multiply traps on signed overflow. On x86-64 the multiply is followed by `jno; ud2` unless the node's type wraps (`int-trap-after`, `X86_64.codex`), and the zig plug checks it the same way.

`rnd`'s second multiply, `b * 1274126177`, leaves the Integer range for any input above 17. Computed over −100,000 to 100,000, it stays in range only for −1 through 17. The app passes larger inputs from the start:
- `rnd`'s first call is from `seed-scene`, which the opening runs before the first frame. Its first `spawn-burst`, centred at (300 × 256, 170 × 256) with i = 0, calls `rnd 207360`, where the product is about 9.9 × 10²². The app stops there.
- `maybe-launch` passes `frame * 17 + 3`: 3 at frame 0, then 156 at frame 9 and 309 at frame 18 (`launch-every` is 9), and both of those overflow.
- The finale's inputs are larger still.

For every input where the plain multiply stays in range, the wrapping `rnd` returns the value it returned before.

**History.**
- `rnd` has multiplied this way since Update 32 (`55be4d3a`), before the contract existed.
- The same hash multiply trapped in the web app's skyline module on 2026-09-03, under the COMPILER-36 plug (`apps/fireworks/fw-verify.mjs`, `apps/landing/build.ps1`). `FireworksShow`'s `w64-mul` is the fix for that. The bare-metal app's `rnd` was not changed with it.

**How it was found.** Our port runs Cobblestone's screen programs as Codex emitted to Roc, on a zig host that carries codex-vm's GPU (`framebuffer/` in github.com/showell/roc-apps, at `2fa163c`). There Update 60's Fireworks stopped with `Integer multiplication overflowed` before its first frame.

**Verified.**

1. **The trap, in a probe,** as `plugs-backlog.md` 2.21's grading note asks: one program, run several times with only `rnd` changed.
   - The compiler is Update 60's zig plug: `codexzig`, Update 60's compiler and zig plug, which our transpiler builds from `9fff850c` into a native tool, its emitted zig a fixed point.
   - Each version was built with zig 0.16.0 and run.

   This change's version:

       Chapter: RndFixed
         cites Foreword chapter Console
         cites Foreword chapter Wrap64

       Section: Body

         rnd : Integer between -9223372036854775808 and 9223372036854775807 wrapping -> Integer
         rnd (n) =
           let a = n * 374761393 + 668265263
           in let b = bit-xor a (bit-shru a 13)
           in let c = w64-mul b 1274126177
           in bit-and (bit-xor c (bit-shru c 16)) #FFFFFF

         opening : [Console] Nothing = act
           print-line ("rnd 207360 = " & show (rnd 207360))
           print-line ("rnd 3 = " & show (rnd 3))
           print-line ("rnd 7 = " & show (rnd 7))
           print-line ("rnd 984 = " & show (rnd 984))
           print-line ("rnd 2654435 = " & show (rnd 2654435))
         end

   | `rnd` | output |
   |---|---|
   | as in Update 60 (`Integer -> Integer`, `c = b * 1274126177`) | `panic: integer overflow` at `b_ * 1274126177`, before the first line prints |
   | the wrapping parameter alone, `c = b * 1274126177` | the same panic at the same multiply; the emitted zig wraps the first line, `(n_ *% 374761393) +% 668265263` |
   | this change | `8087719`, `9853044`, `2346528`, `3578510`, `13875036` |
   | as in Update 60, printing `rnd` of 3, 7, 17 and 18 | `9853044`, `2346528`, `1582232`, then the panic on 18 |

   The values are 64-bit two's-complement arithmetic, computed separately in Python. Of the inputs:
   - 207360 and 3 are values the app passes: the first burst, and `maybe-launch` at frame 0;
   - 984 is `finale-launch`'s formula at frame 0 with i = 1, and 2654435 is `spawn-burst`'s at the origin with i = 1. Those two are test points, not calls the app makes.

2. **Update 60's front end** (`codexir`, built the same way; source to IR) accepts the chapter on both sides.
   - It reports the same diagnostics for both: three CDX3005 warnings (`is-whitespace`, `is-digit` and `is-letter` shadow builtins) and one info diagnostic.
   - Its IR is where the change shows: `rnd`'s two multiplies are `mul-int` at Update 60 and `mul-int-wrapping` here. That is the mode `int-trap-after` reads, through `int-ty-wraps`.

3. **The app, on our port,** at 1024 × 768:
   - Update 60's stops before its first frame with `Integer multiplication overflowed`.
   - This change's runs a whole cycle of 3,900 GPU flushes (five cities of 600 frames each, then the 900-frame finale), about 52 ms each natively, and exits cleanly. It draws the skyline, the "USA 250 · 1776–2026" banner, the city's name and the bursts, through the cinematic pass the opening turns on (port 0x410).
   - On a second run, the frames the checker numbers 29 and 119 hash as they did on the first.

**Not verified.**
- codex-vm and bare metal: the x86 trap is read from the back end and the IR, not run.
- The app's F1 mode: the fade clear at port 0x40E and its photoreal render.
- `FireworksShow.codex`, which this change does not touch.

**One thing a reviewer may trip on.** `ZigEmitter.codex` still carries prose at lines 602–605 saying that Integer arithmetic wraps and that the integer rows carry the wrapping forms. Its prose at lines 1359–1362 states the COMPILER-36 contract, which is what the plug does, and what the probe shows.

No backlog row: this change fixes what it finds, and `fireworks-backlog.md` has no entry for `rnd`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_0127WrVAaJDy6hZL3pPqoJPk
