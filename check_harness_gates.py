#!/usr/bin/env python3
"""Both harnesses copy two lists from the driver. Keep the copies honest.

`ast/CodexIrHarness.codex` and `ast/CodexZigHarness.codex` stand in for
`opening.codex`, which cannot be bundled beside them because it defines
`opening` itself. So each copies two things the driver owns: the set of IR
emit roots, and the set of diagnostic bags it merges before deciding whether
to emit at all.

A copy drifts. This tree has paid for that twice in one day:

  * the emit-roots list drifted from upstream's six to our four in BOTH
    harnesses, so no oracle could see it -- being wrong together looks
    exactly like being right;
  * the error gate existed in one harness and not the other, and the
    ungated one was used all night as an oracle. It produced a false
    report to Damian's compiler lane, twice, before the difference was
    noticed.

So this compares the two harnesses against EACH OTHER and against the
driver. Agreeing with each other is necessary and not sufficient -- the
emit-roots incident is exactly the case where both agreed and both were
wrong -- which is why the driver is consulted when it can be found.

Exit 1 on any difference. No arguments.
"""
import re
import sys
import pathlib

T = pathlib.Path(__file__).resolve().parent
HARNESSES = {
    "ir": T / "ast" / "CodexIrHarness.codex",
    "zig": T / "ast" / "CodexZigHarness.codex",
}


def emit_roots(text):
    m = re.search(r"-emit-roots\s*=\s*\[(.*?)\]", text, re.S)
    return None if m is None else sorted(re.findall(r'"([^"]*)"', m.group(1)))


def merged_bags(text):
    m = re.search(r"bag-merge-all\s*\[(.*?)\]", text, re.S)
    if m is None:
        return None
    return sorted(p.strip() for p in m.group(1).split(",") if p.strip())


def driver_roots():
    """opening.codex, if CODEX_ROOT points at a tree that has it."""
    import os
    root = os.environ.get("CODEX_ROOT")
    if not root:
        return None
    for p in pathlib.Path(root).rglob("opening.codex"):
        m = re.search(r"ir-emit-roots\s*=\s*\[(.*?)\]", p.read_text(errors="replace"), re.S)
        if m:
            return sorted(re.findall(r'"([^"]*)"', m.group(1)))
    return None


def emit_call_wrappers(text):
    """What the emit call wraps its two arguments in.

    A THIRD thing the harnesses copy from the driver, and the one that got
    away: not a list but the SHAPE of the emit call itself. The driver reads

        emit-ir-chapter (ir-prune-unreachable-roots ...) meta
                        (ir-prune-unreachable-typedefs ... (fe.type-defs))

    and each harness writes its own version of that line. On 2026-08-28 a
    compiler change added the type-def prune to the driver, the harnesses kept
    the old two-argument shape, and every corpus program came out unpruned --
    while the gate checking the result was clean, because nothing had been
    removed. A gate that passes because the change never ran looks exactly
    like a gate that passes because the change is right.

    So: the names wrapped around the chapter and around the type-defs, as
    sets. Comparing names rather than the literal line lets a harness bind an
    intermediate (`let pruned = ...`) without tripping this.
    """
    i = text.find("emit-ir-chapter")
    if i < 0:
        return None
    # A WINDOW, not a forward scan. Both the driver and the harnesses now bind
    # the pruned chapter with `let` before calling, so the names sit BEFORE
    # the call as often as inside it. The first version scanned forward only
    # and reported the driver as applying no prunes at all.
    seg = text[max(0, i - 600):i + 400]
    return sorted(set(re.findall(r"\b(ir-prune-unreachable[a-z-]*)\b", seg)))


def driver_emit_call():
    """The same, from opening.codex, if CODEX_ROOT names a tree with it."""
    import os
    root = os.environ.get("CODEX_ROOT")
    if not root:
        return None
    for p in pathlib.Path(root).rglob("opening.codex"):
        t = p.read_text(errors="replace")
        # Skip the `cites` line, which names every import including the
        # prunes and would otherwise look like the richest call in the file.
        body = "\n".join(l for l in t.split("\n")
                          if "cites " not in l and not l.strip().startswith("("))
        if "emit-ir-chapter" in body:
            return emit_call_wrappers(body)
    return None


def main():
    bad = []
    got = {}
    for name, path in HARNESSES.items():
        if not path.exists():
            bad.append(f"{path} is missing")
            continue
        text = path.read_text()
        got[name] = (emit_roots(text), merged_bags(text), emit_call_wrappers(text))
        if got[name][0] is None:
            bad.append(f"{path.name}: no emit-roots list found")
        if got[name][1] is None:
            bad.append(f"{path.name}: NO ERROR GATE -- no bag-merge-all call")
        if got[name][2] is None:
            bad.append(f"{path.name}: no emit-ir-chapter call found")

    if len(got) == 2 and all(v[0] is not None for v in got.values()):
        if got["ir"][0] != got["zig"][0]:
            bad.append(f"emit roots differ:\n    ir  {got['ir'][0]}\n    zig {got['zig'][0]}")
    if len(got) == 2 and all(v[1] is not None for v in got.values()):
        if got["ir"][1] != got["zig"][1]:
            bad.append(f"merged bags differ:\n    ir  {got['ir'][1]}\n    zig {got['zig'][1]}")

    if len(got) == 2 and all(v[2] is not None for v in got.values()):
        if got["ir"][2] != got["zig"][2]:
            bad.append(f"emit-call wrappers differ:\n    ir  {got['ir'][2]}\n    zig {got['zig'][2]}")
    dc = driver_emit_call()
    if dc is not None:
        for name in got:
            if got[name][2] is not None and got[name][2] != dc:
                bad.append(f"{name} harness emit call wraps {got[name][2]} "
                           f"but the DRIVER wraps {dc} -- a prune the driver "
                           f"applies and this harness does not is invisible to "
                           f"every oracle built on it")

    dr = driver_roots()
    if dr is None:
        print("  note: opening.codex not consulted (set CODEX_ROOT to check against the driver)")
    else:
        for name in got:
            if got[name][0] is not None and got[name][0] != dr:
                bad.append(
                    f"{name} emit roots differ from the DRIVER:\n"
                    f"    {name:3} {got[name][0]}\n    drv {dr}"
                )

    if bad:
        print("HARNESS DRIFT:")
        for b in bad:
            print("  " + b)
        return 1
    print(f"  emit call wraps: {', '.join(got['ir'][2]) or '(nothing)'}")
    print(f"  harness gates agree: {len(got['ir'][0])} emit roots, "
          f"{len(got['ir'][1])} bags merged, both harnesses gated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
