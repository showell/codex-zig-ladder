#!/usr/bin/env python3
"""Does zig_plug_pages.txt still name every page of Chapter: Zig Emitter?

A chapter that spans k > 1 files carries `Page N of M` at each foot (CDX3004).
The bundlers read the LIST, so a page the list does not name is simply absent
from the bundle and every definition on it reads as undefined -- 17 of them,
measured 2026-09-03, all naming `emit-zig-expr`.

Refuses when the list and the directory disagree in either direction.
"""
import os, pathlib, re, sys

CHAPTER = 'Zig Emitter'


def pages_from_list(ladder):
    out = []
    for line in (ladder / 'zig_plug_pages.txt').read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            out.append(line)
    return out


def pages_on_disk(plug_dir):
    found = {}
    for f in sorted(plug_dir.glob('*.codex')):
        head = f.read_text()[:4096]
        m = re.search(r'^Chapter:[ \t]*(.+?)[ \t]*$', head, re.M)
        if m and m.group(1) == CHAPTER:
            tail = f.read_text().rstrip().splitlines()[-1].strip()
            found[f.stem] = tail
    return found


def main():
    codex = pathlib.Path(os.environ.get('CODEX_ROOT', ''))
    if not codex.is_dir():
        sys.exit('CODEX_ROOT is not set to a checkout')
    ladder = pathlib.Path(__file__).parent
    listed = pages_from_list(ladder)
    disk = pages_on_disk(codex / 'codex' / 'plugs' / 'zig')

    bad = 0
    missing = [p for p in disk if p not in listed]
    extra = [p for p in listed if p not in disk]
    for p in missing:
        print(f'RED  {p}.codex declares Chapter: {CHAPTER} and the list does not name it')
        bad += 1
    for p in extra:
        print(f'RED  the list names {p} and no such page declares Chapter: {CHAPTER}')
        bad += 1

    # M in `Page N of M` must equal the number of pages, or the compiler says
    # CDX3004 -- and it says it about the SOURCE, so a wrong M is not something
    # a bundle can paper over.
    n = len(disk)
    for p, marker in sorted(disk.items()):
        want = f'Page {listed.index(p) + 1} of {n}' if n > 1 and p in listed else 'Page 1'
        if marker != want:
            print(f'RED  {p}.codex foot is "{marker}", expected "{want}"')
            bad += 1

    if bad:
        print(f'FAIL: {bad} problem(s); the bundlers read zig_plug_pages.txt')
        return 1
    print(f'ok  {n} page(s) of "{CHAPTER}", listed and numbered consistently: '
          + ', '.join(listed))
    return 0


if __name__ == '__main__':
    sys.exit(main())
