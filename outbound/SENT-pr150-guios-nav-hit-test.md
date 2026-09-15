Title: GuiOS: a sidebar click selects the button under it, and the next frame draws the new pane
URL: https://github.com/damiant3/Cobblestone/pull/150

Branch: showell/NewRepository `guios-nav-hit-test` (`68454f54`), three commits
on Update 60 (`9fff850c`); worktree `cobblestone-guios`.

How it was found: roc-apps' framebuffer platform ran GuiOS; a click on Circuits
queued into the runner showed Settings. The native checker's `-mouse` and
`-ppm` (roc-apps `e492bbf`) measured it.

The description was read cold twice by a fresh agent given the repositories.
The first pass found the glow pixel mislabelled, the click areas and the glow
claims stated more generally than measured, and instruments unexplained. The
second found Dashboard's rows (13-59), "settles at frame 5" true only entry by
entry, the linked roc-apps tree uncommitted, and unrun claims. All addressed,
and a test line added (`68454f54`). The send is the text below.

---

*Written by Claude (Anthropic), working with Steve Howell, on his account and at his direction.*

**What changes.** Three commits on Update 60 (`9fff850c`). Test paths below are under `codex/test/`.

1. **`codex/foreword/ui/AppRunner.codex`:** `bare-app-set-root` passes the new state through `orch-relayout`, so the new root has bounds before the next tick. One line of code, and its prose.
2. **`apps/cvmm/GuiOpening.codex`:**
   - `shell-handle-click` asks `event-target-from-mouse`, over the tree the tick just laid out, which widget the click landed on.
   - A new `shell-nav-index` turns a `nav-<i>` id into that entry's index, or -1.
   - `shell-nav-click` takes that index in place of `(my - 36) / 24`.
   - The `mx < gui-sidebar-w` test goes. Every click is hit-tested, and a widget other than a nav button gives -1, which changes nothing.
3. **`lib/app-runner-frame`:** a line printing the root's bounds after the ticks and after `bare-app-set-root`, and its `.expected`.

**Why, 1: a click selects the wrong entry.** At Update 60 GuiOS draws its three nav buttons at 1024 × 768 as boxes on rows 62–82, 92–112 and 122–142, measured from the frame. `(my - 36) / 24`, whose division truncates toward zero, maps rows to entries differently:

| rows | entry |
|---|---|
| up to 12 | none |
| 13–59 | Dashboard |
| 60–83 | Circuits |
| 84–107 | Settings |
| 108 on | none |

Measured at x = 90, a click on the drawn Dashboard selects Circuits, one on the drawn Circuits selects Settings (or nothing in its lowest rows), and one on the drawn Settings does nothing. Dashboard is reachable only by clicking the rows of the logo and separator above it.

`event-target-from-mouse` is the hit test Orchestrator already uses for mouse events. `widget-button` has no children, so for a click on a button it returns the button, with the id `shell-build-nav-items` gave it.

On this branch a button answers over its layout bounds, which include the terminal theme's margin:
- Circuits answers rows 90–113 and Settings rows 120–143, two rows above and one below each drawn box;
- rows 84–89, 114–119 and 144 on select nothing.

**Why, 2: the frame after a click draws no widget.** GuiOpening's loop ticks, which lays the tree out, then handles input, then renders. A click sets a new root, whose widgets have no bounds until the next tick's `orch-relayout`, so the render right after it draws none of them.

In the measurements below, where the click arrives before the first frame, that frame is entirely background, and the glow then stays off for three more frames. codex-vm measures the glow's distance field on flushes 1, 5, 9 and so on, or when it has none: `tools/codex-vm.c`, the counter at line 14665 and the test at line 14751. The comment above that line says every 8 frames; the code tests every 4. Our port does the same, and here the flush that measured the field was the blank one.

From reading codex-vm and our port, not from a run (our checker hands input over only before the first frame):
- a root change landing on another flush would keep the previous field, and show the old layout's glow over a blank frame;
- on this branch the frame is drawn, but the field can still lag a root change by up to three flushes. That is the glow's cadence, and this change does not touch it.

**How it was found.** Our port runs GuiOS as Codex emitted to Roc, on a zig host that carries codex-vm's GPU and mouse ports. It is `framebuffer/` in github.com/showell/roc-apps, at `2fa163c`. In a WebAssembly build of it, a click on Circuits showed the Settings pane. The port's native checker takes a mouse press and release before the program's first frame and prints each frame's hash.

**Verified,** on that port, not on codex-vm. GuiOpening was built from Update 60 and from this branch and run as `native -screen 1024 768 1024 -mouse 90 <row> 1 -mouse 90 <row> 0 -flushes 6`; the row without a click runs with no `-mouse`.
- **Which entry is selected** is read from the fill at (100, 70), (100, 100) and (100, 130): 85,170,255 selected, 51,204,51 not.
- **The glow** is read at (3, 3), the background pixel inside the root panel's top-left corner: 36,61,139 with it, 16,16,16 without.
- **Frames are counted from 1**; the checker prints them from 0.

| click | Update 60, frames 1–6 | this branch, frames 1–6 |
|---|---|---|
| none | Dashboard, glow, all six (`1f50b26c`) | the same, all six (`1f50b26c`) |
| Dashboard (row 72) | frame 1 blank (`fdfc9dc5`), frames 2–4 Circuits without glow (`bd9fe061`), 5–6 Circuits with glow (`0b34bef5`) | Dashboard, glow, all six (`1f50b26c`) |
| Circuits (row 102) | frame 1 blank (`fdfc9dc5`), frames 2–4 Settings without glow (`da218add`), 5–6 Settings with glow (`8ec94b75`) | Circuits, glow, all six (`0b34bef5`) |
| Settings (row 132) | Dashboard, glow, all six (`1f50b26c`) | Settings, glow, all six (`8ec94b75`) |

Each entry's image on this branch is, hash for hash, the one Update 60 reaches at frame 5 when it selects that entry. On this branch the Circuits pane shows the "Circuits EDA" header and body.

Also run:
- **The new line in `lib/app-runner-frame`,** under Update 60's zig plug. That is `codexzig`, Update 60's compiler and zig plug, which our transpiler builds from `9fff850c` into a native tool.

      Update 60:    set-root bounds: before=0,0 640x480 after=0,0 0x0
      this branch:  set-root bounds: before=0,0 640x480 after=0,0 640x480

  - The Update 60 line comes from this branch's test file, compiled against Update 60's chapters.
  - On this branch, `lib/app-runner-frame` and `forewords/foreword-apprunner` match their `.expected` under the zig plug.
  - The test's root is a label with no children, so the line shows that the new root is laid out and says nothing about children.
  - GuiOpening's hit test has no test of its own; its evidence is the table above.
- **Update 60's front end** (`codexir`, built the same way; source to IR) accepts this branch's GuiOpening, AppRunner and all. It reports one info diagnostic, as it does for Update 60's GuiOpening; the text is not shown, so only the count is compared.
- **`apps/foreword-all-compile`** is refused by the zig plug on both sides alike, `CODEGEN-HALTED: 2 error(s)`, the first `CDX3002 Undefined name: md-doc`. It matches on both under the interpreter in our Rust Codex compiler, a separate implementation.

**What it costs.**
- `bare-app-set-root` now lays the tree out once per call.
- The next tick lays out again only when something has marked the state dirty, and every dispatched event does. So over a click, a press and then a release, a root change costs three whole-tree layouts where Update 60 spent two. Not timed.
- `lib/app-runner-frame`'s existing `set-root:` line prints the same on both sides.

**Not verified.** codex-vm, the Cobblestone battery, and bare metal.

`annotations/AUDITED.txt` lists `codex\test\lib\app-runner-frame.codex` (`reek 2026-08-05`). This change leaves that entry as it is.

No backlog row: nothing is left open, and neither `apps/cvmm/cvmm-backlog.md` nor `apps/guios/guios-backlog.md` has an entry for it.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_0127WrVAaJDy6hZL3pPqoJPk
