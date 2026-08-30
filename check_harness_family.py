#!/usr/bin/env python3
"""The driver-standin harness exists in more than one repository. Compare them.

    ./check_harness_family.py            the two this repo owns
    ./check_harness_family.py <a> <b>    any copies, e.g. a worktree's
    ./check_harness_family.py a.codex b.codex ...

Each stands in for `opening.codex` for a different tool -- `codexzig` here and
in codex-zig-transpiler, `codexwasm` in safari-codex -- and each was written by
copying the last one. What they may legitimately differ in: their prefix
(`czg-`, `cwm-`), their prose, and what they emit at the end. What they must NOT
differ in is WHICH DIAGNOSTICS THEY SEE, because that is not about the tool.

This replaces check_harness_twin.py's line-for-line comparison, which could only
ever hold two of them: the wasm copy uses a different prefix throughout and a
different emitter call, so a straight diff calls it divergent when it agrees
about everything that matters.

WHY THIS EXISTS. On 2026-08-30 the zig harness merged four bags copied
faithfully from the driver, and those four were never the driver's list --
`opening.codex:479-482` builds three more itself, one of which carries CDX3006,
the cross-chapter collision. Ten real instances hid behind that in a port that
was green its whole life, and the error gate was letting duplicate-cite through
for the same reason. A defect that arrives by copying is a defect that arrives
in every copy.
"""
import pathlib, re, sys

HOME = pathlib.Path.home() / 'showell_repos'
# The two copies THIS repository is responsible for. Pass paths explicitly to
# compare others -- and pass the WORKTREE you mean, not the transpiler's main
# checkout, which sits on whatever branch it sits on.
#
# safari-codex's CodexWasmHarness.codex is a third copy and is deliberately NOT
# listed: codexwasm is in discovery as of 2026-08-30 and will be packaged by the
# session that owns it. Add it here when it settles.
KNOWN = [
    HOME / 'codex-zig-ladder' / 'ast' / 'CodexZigHarness.codex',
    HOME / 'codex-zig-transpiler' / 'source' / 'CodexZigHarness.codex',
]
PREFIX = re.compile(r'\b(czg|cwm|irc)-')


def bags(path):
    """The bag names merged into the halt gate, prefix-normalised and sorted."""
    text = pathlib.Path(path).read_text()
    m = re.search(r'bag-merge-all \[(.*?)\]', text, re.S)
    if not m:
        return None
    return sorted(PREFIX.sub('X-', b.strip()) for b in m.group(1).split(','))


def reports_notices(path):
    """Does it write the non-error diagnostics anywhere, or only halt on errors?"""
    t = pathlib.Path(path).read_text()
    return 'write-binary' in t and 'text-to-utf8-bytes' in t


def main():
    paths = [pathlib.Path(a) for a in sys.argv[1:]] or KNOWN
    rows, missing = [], []
    for p in paths:
        if not p.is_file():
            missing.append(p); continue
        rows.append((p, bags(p), reports_notices(p)))
    for p in missing:
        print(f'  SKIPPED (absent): {p}')
    if len(rows) < 2:
        print('need at least two harnesses to compare'); return 1

    ref_bags = rows[0][1]
    rc = 0
    print(f'{"harness":58} {"bags":>5}  notices')
    for p, b, n in rows:
        tag = str(p).replace(str(HOME) + '/', '')
        print(f'  {tag:56} {len(b) if b else "?":>5}  {"yes" if n else "NO"}')
        if b != ref_bags:
            rc = 1
        if not n:
            rc = 1
    if rc == 0:
        print(f'\nall {len(rows)} agree: same {len(ref_bags)} bags, all report non-errors')
        for b in ref_bags:
            print(f'    {b}')
        return 0

    print('\nDIVERGENT. The bag list is not about which tool this is.')
    for p, b, n in rows:
        if b != ref_bags:
            print(f'  {p.name} bags: {b}')
        if not n:
            print(f'  {p.name} does not report non-error diagnostics at all')
    return rc


if __name__ == '__main__':
    sys.exit(main())
