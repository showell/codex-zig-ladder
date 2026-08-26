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


def main():
    bad = []
    got = {}
    for name, path in HARNESSES.items():
        if not path.exists():
            bad.append(f"{path} is missing")
            continue
        text = path.read_text()
        got[name] = (emit_roots(text), merged_bags(text))
        if got[name][0] is None:
            bad.append(f"{path.name}: no emit-roots list found")
        if got[name][1] is None:
            bad.append(f"{path.name}: NO ERROR GATE -- no bag-merge-all call")

    if len(got) == 2 and all(v[0] is not None for v in got.values()):
        if got["ir"][0] != got["zig"][0]:
            bad.append(f"emit roots differ:\n    ir  {got['ir'][0]}\n    zig {got['zig'][0]}")
    if len(got) == 2 and all(v[1] is not None for v in got.values()):
        if got["ir"][1] != got["zig"][1]:
            bad.append(f"merged bags differ:\n    ir  {got['ir'][1]}\n    zig {got['zig'][1]}")

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
    print(f"  harness gates agree: {len(got['ir'][0])} emit roots, "
          f"{len(got['ir'][1])} bags merged, both harnesses gated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
