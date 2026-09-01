#!/usr/bin/env python3
"""Canonicalise Codex IR text so two front ends can be compared honestly.

    ./canon_ir.py a.ir                 canonical form to stdout
    ./canon_ir.py --cmp a.ir b.ir      exit 0 if canonically equal
    ./canon_ir.py --selftest           the soundness checks, on any .ir given

WHY THIS EXISTS. The IR text publishes the type checker's UNIFICATION VARIABLE
NUMBERS. `(tvar 16)` is a type variable and the trailing integer of
`(row (labels ...) "" 467)` is `row.tail-id`; across the banked corpus there
are 8,841 of the first and 18,228 rows, with ids into the thousands. Those
numbers are a function of the ORDER in which the checker allocated fresh
variables over the whole program, not of the program's meaning. Requiring a
second implementation to reproduce them is requiring it to reproduce the walk,
which forecloses ever improving the walk.

So the standing gate is CANONICAL equality -- ids renumbered in order of first
appearance -- and byte-identity is tracked separately as a ratchet. An
alpha-equivalent IR is a correct IR.

WHAT IS DELIBERATELY NOT RENUMBERED. Only two positions carry allocator ids:
the argument of `(tvar N)` and the LAST element of a `(row ...)` form. Every
other integer in the IR means something -- `(int-lit 5)` is a literal,
`(int 0 100 ov-clamp)` is a bounded range, the two trailing integers of a
`(def ...)` are prose offsets, and `"p/0"` is a field slot inside a string.
Renumbering by regex over bare integers would silently destroy all of them,
which is why this parses the s-expression instead.

THE TWO FAMILIES ARE NUMBERED SEPARATELY and neither is renumbered across
files: canonicity is per program, because that is the unit being compared.

SOUNDNESS IS CHECKED, NOT ASSERTED (`--selftest`). A canonicaliser that
mapped everything to one symbol would make every comparison pass, and a green
run would look exactly the same. So the selftest requires it to be idempotent,
to be invariant under a permutation of the ids, AND to still tell two
structurally different programs apart.
"""

import argparse
import pathlib
import random
import re
import sys

ATOM = re.compile(r'[^\s()"]+')


def parse(text):
    """The IR as nested lists. Strings keep their quotes: they are atoms here,
    never containers, and `"p/0"` must not be looked inside."""
    i, n = 0, len(text)
    stack, cur = [], []
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif c == '(':
            stack.append(cur); cur = []; i += 1
        elif c == ')':
            done = cur
            if not stack:
                raise ValueError(f'unbalanced ) at {i}')
            cur = stack.pop(); cur.append(done); i += 1
        elif c == '"':
            j = i + 1
            while j < n:
                if text[j] == '\\':
                    j += 2; continue
                if text[j] == '"':
                    break
                j += 1
            cur.append(text[i:j + 1]); i = j + 1
        else:
            m = ATOM.match(text, i)
            cur.append(m.group(0)); i = m.end()
    if stack:
        raise ValueError('unbalanced (')
    return cur


def render(node):
    if isinstance(node, str):
        return node
    return '(' + ' '.join(render(x) for x in node) + ')'


def _sites(node, out):
    """Every position holding an allocator id, in document order.

    A tvar's id is element 1 of `(tvar N)`. A row's tail-id is the LAST
    element of `(row ...)`. Both are found by walking, so a bare integer
    anywhere else is never touched.
    """
    if isinstance(node, str):
        return
    if node and node[0] == 'tvar' and len(node) == 2 and node[1].lstrip('-').isdigit():
        out.append((node, 1, 'tvar'))
    elif node and node[0] == 'row' and len(node) >= 2 and node[-1].lstrip('-').isdigit():
        out.append((node, len(node) - 1, 'row'))
    for x in node:
        _sites(x, out)


def canon(text):
    """Renumber both id families in order of first appearance."""
    tree = parse(text)
    sites = []
    _sites(tree, sites)
    maps = {'tvar': {}, 'row': {}}
    for node, idx, fam in sites:
        m = maps[fam]
        old = node[idx]
        if old not in m:
            m[old] = str(len(m))
        node[idx] = m[old]
    return '\n'.join(render(x) for x in tree) + '\n'


def permute(text, seed=7):
    """An alpha-renaming: the same program with its ids shuffled."""
    tree = parse(text)
    sites = []
    _sites(tree, sites)
    rng = random.Random(seed)
    for fam in ('tvar', 'row'):
        olds = sorted({node[idx] for node, idx, f in sites if f == fam}, key=int)
        news = olds[:]
        rng.shuffle(news)
        m = dict(zip(olds, news))
        for node, idx, f in sites:
            if f == fam:
                node[idx] = m[node[idx]]
    return '\n'.join(render(x) for x in tree) + '\n'


def selftest(paths):
    ok = True
    for p in paths:
        t = pathlib.Path(p).read_text(errors='replace')
        c = canon(t)
        # 1. IDEMPOTENT. Canonicalising twice must add nothing.
        if canon(c) != c:
            print(f'  FAIL idempotent      {p}'); ok = False
        else:
            print(f'  pass idempotent      {p}')
        # 2. INVARIANT under an alpha-renaming. This is the property the gate
        #    is for: the same program with other numbers must compare equal.
        if canon(permute(t)) != c:
            print(f'  FAIL rename-invariant {p}'); ok = False
        else:
            print(f'  pass rename-invariant {p}')
        # 3. DISCRIMINATING. A canonicaliser that erased everything would pass
        #    1 and 2 and make every future comparison meaningless. Perturb one
        #    literal by the smallest amount that must matter and require the
        #    canonical forms to differ.
        bumped = t.replace('(int-lit 0)', '(int-lit 99)', 1)
        if bumped == t:
            bumped = t.replace('(bool-lit true)', '(bool-lit false)', 1)
        if bumped == t:
            print(f'  ---- discriminating   {p} (no literal to perturb)')
        elif canon(bumped) == c:
            print(f'  FAIL discriminating   {p} -- a changed literal survived canonicalisation'); ok = False
        else:
            print(f'  pass discriminating   {p}')
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--cmp', action='store_true', help='compare two files canonically')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest(a.paths) else 1
    if a.cmp:
        if len(a.paths) != 2:
            raise SystemExit('--cmp takes exactly two files')
        x, y = (canon(pathlib.Path(p).read_text(errors='replace')) for p in a.paths)
        print('canonically EQUAL' if x == y else 'canonically DIFFERENT')
        return 0 if x == y else 1
    sys.stdout.write(canon(pathlib.Path(a.paths[0]).read_text(errors='replace')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
