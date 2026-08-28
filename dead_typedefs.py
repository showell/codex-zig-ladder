"""Dead top-level declarations in the PROGRAM region, split by what they are.

Excludes names zig resolves for itself -- `main`, `cx_entry` -- which are not
dead, merely unreferenced. That is the same blind spot the shake's corpus gate
has, and the first pass at this fell straight into it: it reported `main` dead
in 578 of 578 programs.
"""
import glob, pathlib, re, sys
from collections import Counter

BANNER = '// THE PRELUDE. Everything ABOVE this line is the transpiled program.'
NAME_RESOLVED = {'main', 'cx_entry', '_start', 'panic', 'std_options'}
TYPECTOR = re.compile(r'(?m)^fn ([A-Z][A-Za-z0-9_]*)\(comptime .*\) type \{')
TYPEDEF  = re.compile(r'(?m)^const ([A-Za-z_][A-Za-z0-9_]*) = (?:struct|\*|enum|union)')
ANYDECL  = re.compile(r'(?m)^(?:pub )?(?:fn|const) ([A-Za-z_][A-Za-z0-9_]*)')

kinds = {'type constructor': Counter(), 'type def': Counter(), 'value def': Counter()}
live = Counter(); files = 0; bytes_dead = Counter()
for f in sorted(glob.glob(sys.argv[1])):
    body = pathlib.Path(f).read_text(errors='replace')
    i = body.find(BANNER)
    prog = body[:i] if i >= 0 else body
    files += 1
    ctors = set(TYPECTOR.findall(prog)); tdefs = set(TYPEDEF.findall(prog))
    for m in ANYDECL.finditer(prog):
        n = m.group(1)
        if n in NAME_RESOLVED: continue
        k = 'type constructor' if n in ctors else 'type def' if n in tdefs else 'value def'
        if len(re.findall(r'\b' + re.escape(n) + r'\b', prog)) == 1:
            kinds[k][n] += 1
            j = prog.find('\n\n', m.start())
            bytes_dead[k] += (j if j > 0 else len(prog)) - m.start()
        else:
            live[k] += 1

print(f'{files} programs. Dead = the name appears only at its own declaration.\n')
print(f'{"kind":18} {"dead":>7} {"live":>7} {"dead bytes":>12}')
for k in kinds:
    print(f'{k:18} {sum(kinds[k].values()):7,} {live[k]:7,} {bytes_dead[k]:12,}')
print(f'\ntop dead type constructors / type defs:')
for k in ('type constructor', 'type def'):
    for n, c in kinds[k].most_common(6):
        print(f'    [{k[:4]}] {n:26} dead in {c:4}/{files}')
