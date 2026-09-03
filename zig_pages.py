#!/usr/bin/env python3
"""The pages of Chapter: Zig Emitter, for the scripts that read its source.

`ZigEmitter.codex` was the whole emitter until 2026-09-03. It is now page 1 of
four, and the things these scripts look for did not all stay on it: the
`ZigBuiltinEmitter` table moved to ZigEmitterExpressions.codex and
`zig-prelude-parts` to ZigPrelude.codex. A script still reading page 1 alone
finds NOTHING and reports nothing missing, which is the failure mode worth
naming -- it does not crash, it agrees with you.

`text()` returns the pages concatenated, in list order, which is what a script
scanning for definitions wants. `paths()` returns them separately for a script
that needs to say WHICH file a hit came from.
"""
import os, pathlib

LADDER = pathlib.Path(__file__).parent
LIST = LADDER / 'zig_plug_pages.txt'


def names():
    out = []
    for line in LIST.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            out.append(line)
    if not out:
        raise SystemExit(f'{LIST} names no pages')
    return out


def paths(codex_root=None):
    root = pathlib.Path(codex_root or os.environ.get('CODEX_ROOT', ''))
    if not root.is_dir():
        raise SystemExit('CODEX_ROOT is not set to a checkout')
    d = root / 'codex' / 'plugs' / 'zig'
    out = []
    for n in names():
        p = d / f'{n}.codex'
        if not p.is_file():
            raise SystemExit(f'{p} is listed in {LIST.name} and does not exist')
        out.append(p)
    return out


def text(codex_root=None):
    return '\n'.join(p.read_text() for p in paths(codex_root))


if __name__ == '__main__':
    for p in paths():
        print(p)
