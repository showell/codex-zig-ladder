#!/usr/bin/env python3
"""The typed-IR application rule, over two IR trees of the same programs.

In (apply F A T), F's type must be (fn P R ...) with P agreeing with A's type
and R with T; in (list-expr (elems ...) E) each element's type agrees with E
and carries no `error`. (tvar N) agrees with anything: an unresolved variable says it
does not know. A site that disagrees at U61 and agreed at U60 is a closure to
int-default that a neighbouring node contradicts.

    apply_check.py <u60-dir> <u61-dir>
"""
import pathlib
import re
import sys
from collections import Counter

TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


def parse(text):
    stack = [[]]
    for t in TOKEN.findall(text):
        if t == '(':
            stack.append([])
        elif t == ')':
            if len(stack) == 1:
                continue
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(t)
    while len(stack) > 1:
        done = stack.pop()
        stack[-1].append(done)
    return stack[0]


LIT = {'int-lit': 'int-default', 'text-lit': 'text', 'bool-lit': 'boolean',
       'char-lit': 'char', 'num-lit': 'real'}
TYPED_LAST = {'name', 'apply', 'binary', 'if', 'match', 'field-access',
              'record', 'act', 'lambda', 'negate', 'error'}


def type_of(e):
    """The type an expression node carries, or None when this reader cannot say."""
    if not isinstance(e, list) or not e:
        return None
    h = e[0]
    if h in LIT:
        return LIT[h]
    if h == 'let' and len(e) >= 3:
        return e[2]
    if h == 'list-expr' and len(e) >= 3:
        return ['list', e[2]]
    if h in TYPED_LAST and len(e) >= 2:
        return e[-1]
    return None


def norm(t):
    """Spellings of one type that the wire uses interchangeably: a bounded
    Integer is an Integer, a unit wraps its carrier, and ctd / record-ty /
    sum name the same declared type."""
    if isinstance(t, list) and t:
        if t[0] == 'int':
            return 'int-default'
        if t[0] == 'unit' and len(t) >= 3:
            return norm(t[2])
        if t[0] in ('record-ty', 'sum') and len(t) >= 2:
            return ['ctd'] + t[1:]
    return t


def agree(a, b):
    if a is None or b is None:
        return True
    a, b = norm(a), norm(b)
    if isinstance(a, list) and a[:1] == ['tvar']:
        return True
    if isinstance(b, list) and b[:1] == ['tvar']:
        return True
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b) or a[:1] != b[:1]:
            # effect rows and similar trailing parts: compare heads and the
            # common positional children only for fn; otherwise differ
            if a[:1] == b[:1] == ['fn']:
                return agree(a[1], b[1]) and agree(a[2], b[2])
            return False
        if a[0] == 'row':
            return True
        return all(agree(x, y) for x, y in zip(a[1:], b[1:]))
    return a == b


def fn_parts(t):
    if isinstance(t, list) and t[:1] == ['fn'] and len(t) >= 3:
        return t[1], t[2]
    if isinstance(t, list) and t[:1] == ['effectful']:
        return None
    return None


def walk(node, defname, out):
    if not isinstance(node, list) or not node:
        return
    if node[:1] == ['def'] and len(node) > 1:
        defname = node[1]
    if node[:1] == ['apply'] and len(node) >= 4:
        f, a, t = node[1], node[2], node[3]
        parts = fn_parts(type_of(f))
        if parts:
            p, r = parts
            if not agree(p, type_of(a)):
                out.append((defname, 'arg', show(f), show(p), show(type_of(a))))
            if not agree(r, t):
                out.append((defname, 'result', show(f), show(r), show(t)))
    if node[:1] == ['list-expr'] and len(node) >= 3 and isinstance(node[1], list):
        want = node[2]
        for el in node[1][1:]:
            got = type_of(el)
            if not agree(want, got) or got == 'error' or (isinstance(got, list) and 'error' in got):
                out.append((defname, 'element', 'list-expr', show(want), show(got)))
    # a list whose head is a symbol names a node; one whose head is a list
    # (the parser's top level) is a sequence, and every child is walked
    for c in (node if isinstance(node[0], list) else node[1:]):
        walk(c, defname, out)


def show(x, limit=90):
    if isinstance(x, list):
        s = '(' + ' '.join(show(c, 10**6) for c in x) + ')'
    else:
        s = str(x)
    return s if len(s) <= limit else s[:limit] + '...'


def head(f):
    while isinstance(f, list) and f[:1] == ['apply']:
        f = f[1]
    return f[1] if isinstance(f, list) and f[:1] == ['name'] else show(f, 30)


def main():
    d60, d61 = map(pathlib.Path, sys.argv[1:3])
    stats = Counter()
    new_sites = []
    standing = []
    for f61 in sorted(d61.glob('*.ir')):
        f60 = d60 / f61.name
        t61 = f61.read_text(errors='replace')
        t60 = f60.read_text(errors='replace') if f60.is_file() else ''
        if not t61.startswith('(chapter'):
            stats['halted or no IR'] += 1
            continue
        stats['programs'] += 1
        if t60 == t61:
            stats['IR identical'] += 1
            same = []
            walk(parse(t61), None, same)
            standing += [(f61.stem, *x) for x in same]
            continue
        stats['IR moved'] += 1
        # every difference must be (tvar N) -> int-default; anything else is named
        if re.sub(r'\(tvar \d+\)', 'int-default', t60) != t61:
            stats['moved by MORE than tvar->int-default'] += 1
        closures = len(re.findall(r'\(tvar \d+\)', t60)) - len(re.findall(r'\(tvar \d+\)', t61))
        stats['closure tokens'] += closures
        s60, s61 = [], []
        walk(parse(t60), None, s60)
        walk(parse(t61), None, s61)
        old = Counter((x[0], x[1], x[2]) for x in s60)
        for d, k, fshow, want, got in s61:
            key = (d, k, fshow)
            if old[key]:
                old[key] -= 1
                standing.append((f61.stem, d, k, fshow, want, got))
                continue
            new_sites.append((f61.stem, d, k, fshow, want, got))
        if any(x[0] == f61.stem for x in new_sites):
            stats['programs with a contradicted closure'] += 1
    for k in ('programs', 'halted or no IR', 'IR identical', 'IR moved',
              'moved by MORE than tvar->int-default', 'closure tokens',
              'programs with a contradicted closure'):
        print(f'{k:40s} {stats[k]}')
    print(f'{"contradicted sites (new at U61)":40s} {len(new_sites)}')
    print(f'{"standing sites (wrong at U60 too)":40s} {len(standing)}')
    print()
    for prog, d, k, fshow, want, got in standing:
        print(f'STANDING\t{prog}\t{d}\t{k}\t{fshow}\twants {want}\tgot {got}')
    for prog, d, k, fshow, want, got in new_sites:
        print(f'NEW\t{prog}\t{d}\t{k}\t{fshow}\twants {want}\tgot {got}')


if __name__ == '__main__':
    main()
