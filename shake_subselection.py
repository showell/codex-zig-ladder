"""Validate the replacement for check-zig-prelude-surface.ps1's agreement test.

The script today requires every subject's emitted prelude to be IDENTICAL.
Shaking makes them differ by design. The replacement is a stronger property,
not a weaker one: each emitted prelude must be a SUB-SELECTION of one known
whole, in table order -- walk the parts in order, consume the ones that match
at the cursor, skip the rest, and require the cursor to land exactly at the
end. A prelude that reordered, duplicated, truncated or invented anything
fails that walk.

The surface is then derived from the WHOLE rather than from any one program,
which keeps zig-prelude-decls a union, as the emitter's own prose insists.

Validated here in Python, over real shaken output, before porting.
"""
import glob, pathlib, re, sys
sys.path.insert(0, '/home/steve/showell_repos/codex-zig-ladder')
import shake_parts as S

SPD = '/tmp/claude-1000/-home-steve-showell-repos-codex-zig-ladder/ffbda379-6bbc-4daf-bca0-9088218f5737/scratchpad'
BANNER = '// THE PRELUDE. Everything ABOVE this line is the transpiled program.'

parts = S.group(S.read_chunks(pathlib.Path(SPD + '/ZigEmitter.orig.codex')))
texts = [t for _, t in parts]
whole = ''.join(texts)


def sub_selection(emitted):
    """(ok, kept_names) -- emitted must be parts in table order, some omitted."""
    cur, kept = 0, []
    for (name, t) in parts:
        if emitted.startswith(t, cur):
            cur += len(t)
            kept.append(name)
    return cur == len(emitted), kept


files = sorted(glob.glob(sys.argv[1]))
ok = bad = skipped = 0
for f in files:
    body = pathlib.Path(f).read_text(errors='replace')
    i = body.find(BANNER)
    if i < 0:
        skipped += 1
        continue
    # The prelude begins after the banner block; find it by locating the first
    # part text that occurs at or after the banner.
    start = min((body.find(t, i) for t in texts if body.find(t, i) >= 0),
                default=-1)
    if start < 0:
        print(f'  {pathlib.Path(f).name}: no part text after the banner')
        bad += 1
        continue
    good, kept = sub_selection(body[start:])
    if good:
        ok += 1
    else:
        bad += 1
        if bad <= 5:
            print(f'  {pathlib.Path(f).name}: NOT a sub-selection '
                  f'({len(kept)} parts matched)')
print(f'  SUB-SELECTION: {ok} ok, {bad} not, {skipped} no banner, over {len(files)} files')

# And the surface, derived from the whole rather than from any one program.
surface = set()
for line in whole.split('\n'):
    for m in re.finditer(r'\b(?:const|var)\s+([A-Za-z_][A-Za-z0-9_]*)', line):
        surface.add(m.group(1))
    for m in re.finditer(r'\|\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:,\s*([A-Za-z_][A-Za-z0-9_]*)\s*)?\|', line):
        surface.add(m.group(1))
        if m.group(2): surface.add(m.group(2))
    for m in re.finditer(r'\bfn\s+[A-Za-z_][A-Za-z0-9_]*\s*\(([^)]*)\)', line):
        for p in m.group(1).split(','):
            mm = re.match(r'^\s*(?:comptime\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*:', p)
            if mm: surface.add(mm.group(1))
surface.discard('_')
print(f'  surface derived from the WHOLE: {len(surface)} names')
fns = set(re.findall(r'(?m)^(?:pub )?fn ([A-Za-z_][A-Za-z0-9_]*)', whole))
print(f'  function names, which the script never derives: {len(fns)}')
