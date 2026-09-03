#!/usr/bin/env python3
"""Assert the ladder can find everything it needs, without running a rung.

This exists so a path refactor can be cleared in seconds instead of in hour two
of a sweep. Every script here used to derive its roots by counting directories
up from itself, and the two roots it might have wanted -- the ladder's own tree
and the Codex checkout -- happened to be one level apart, so the count silently
carried the answer and the scripts already disagreed about it. Moving the ladder
out of the checkout makes the two unrelated, and every site has to say which one
it meant.

Getting that classification wrong is the whole risk of the move, and it is not a
risk worth discovering from a red rung: a rung reports a diff, and a diff does
not say "you resolved against the wrong root". So the classification is checked
directly. Each thing the ladder opens is named here with the root it belongs to;
if a path does not resolve, this says which one and why in one line.

The second half is the completeness check. A conversion that missed a site is
indistinguishable from a finished one until that site runs, so a leftover
level-count is reported as a failure in its own right rather than left to be
noticed later.

The rule this enforces is narrower than "never count directories", because that
rule cannot be obeyed: a script has to reach ladder_root.py somehow, and the
only thing it knows is where it is. The real rule is that counting may reach the
LADDER and never the CHECKOUT. The ladder's internal layout is fixed and moves
as a unit, so ast/ is always one below the root; the checkout is the thing the
move makes unrelated, and every path to it goes through ladder_root.

So one bootstrap line per script is allowed, and it has to ask: mark it
`ladder-root-bootstrap` and it is skipped. Exemptions are counted and printed
rather than passed over in silence, because an exemption nobody counts is how a
rule stops meaning anything.
"""

import pathlib
import re
import sys

from ladder_root import CODEX, LADDER

# What a checkout has to provide. Tracked in the Codex repository and used
# unmodified; the ladder patches none of it.
FROM_CHECKOUT = [
    ('codex/compiler/opening.codex', 'the compiler driver, and the marker that says this IS a checkout'),
    ('seed/Codex.cdx', 'the seed: the trusted binary every measurement is compared against'),
    ('build/concat-codex-self.ps1', 'used by recon.sh to concatenate the compiler'),
    ('codex/plugs/common/plug-build-lib.ps1', "the author's bundler library, sourced by every bundle_*.ps1"),
    ('codex/plugs/zig/ZigEmitter.codex', 'the plug under test, page 1 of 4'),
    ('codex/plugs/zig/ZigEmitterExpressions.codex', 'page 2: expressions and the builtin table'),
    ('codex/plugs/zig/ZigEmitterApply.codex', 'page 3: lambdas, closures and application'),
    ('codex/plugs/zig/ZigPrelude.codex', 'page 4: the emitted zig runtime'),
    ('codex/test/plug-oracle-arith.codex', "the passes_to_x86_on_arith rung's subject"),
]

# Built by cycle.sh (it stubs the author's compile step and compiles the
# bundle through the seed), NOT tracked. A fresh clone does not have them,
# and the rungs that need them would otherwise fail on a missing file that
# names nothing.
FROM_CYCLE_BUILD = [
    ('codex/plugs/zig/build-output/zig-plug.cdx', 'the TCP arm pushes IR through this'),
    ('codex/plugs/zig/build-output/plug-source.codex', 'the bundled plug source'),
]

# The ladder's own tree.
FROM_LADDER = [
    ('ast/emit_harness.py', 'the shared harness template'),
    ('ast/oracle_lib.sh', 'the rung machinery, and the truth arm'),
    ('ast/plug_arm_lib.sh', "the plug's arms, sourced by oracle_lib.sh"),
    ('ast/allcycles.sh', 'the sweep'),
    ('codex_vm.py', 'the QEMU driver'),
    ('ring_compile.py', 'the ring transport'),
]

# Level-counting, in any of the three languages the ladder is written in. A
# match is a site the move would break, or has already broken.
LEFTOVERS = [
    (r'\.parent\.parent', 'python: counts directories up from __file__'),
    (r'\.parents\[\d+\]', 'python: counts directories up from __file__'),
    (r'dirname[^\n]*\.\.', 'shell: counts directories up from BASH_SOURCE'),
    (r"PSScriptRoot[^\n]*'\.\.'", 'powershell: counts directories up from PSScriptRoot'),
]

SKIP = {'ladder_root.py', 'check_paths.py'}

# A line carrying this is the one sanctioned level-count: the step that finds
# the ladder's own root so ladder_root can be asked for the rest.
BOOTSTRAP = 'ladder-root-bootstrap'


def check_group(entries, root, label, hint=None):
    bad = []
    for rel, why in entries:
        path = root / rel
        if not path.exists():
            bad.append(f'  MISSING {rel}\n    ({why})' + (f'\n    {hint}' if hint else ''))
    print(f'{label}: {len(entries) - len(bad)}/{len(entries)}')
    return bad


def check_leftovers():
    bad, bootstraps = [], []
    for path in sorted(LADDER.rglob('*')):
        if path.suffix not in {'.py', '.sh', '.ps1'} or path.name in SKIP:
            continue
        try:
            text = path.read_text(errors='replace')
        except OSError:
            continue
        lines = text.splitlines()
        for pattern, why in LEFTOVERS:
            for m in re.finditer(pattern, text):
                n = text[:m.start()].count('\n') + 1
                where = f'{path.relative_to(LADDER)}:{n}'
                if BOOTSTRAP in lines[n - 1]:
                    bootstraps.append(f'  {where}')
                else:
                    bad.append(f'  {where}  {why}')
    return bad, bootstraps


def check_table():
    """Warn when the README's banked-against table disagrees with the Update
    derived from the seed on disk (S7). A warning, never a failure: the
    README itself documents the mid-rebank state where the pin runs one
    Update ahead of the table, and that in-between is normal. What this
    catches is the table staying wrong AFTER the new bank lands."""
    m = re.search(r'^\| Update \| (\d+)', (LADDER / 'README.md').read_text(), re.M)
    if not m:
        return ['  WARN: no "| Update | N" row found in README.md to cross-check']
    claimed = int(m.group(1))
    import seed_identity
    derived = seed_identity.update_label(seed_identity.seed_sha256())
    if derived is None:
        return [f'  note: table says Update {claimed}; the seed on disk is '
                'unreleased (no note names it), nothing to cross-check']
    if derived != claimed:
        return [f'  WARN: banked-against table says Update {claimed}, the seed '
                f'on disk derives Update {derived} -- normal mid-rebank; '
                'correct the table when the new bank lands']
    return []


def main():
    print(f'CODEX  {CODEX}')
    print(f'LADDER {LADDER}\n')

    failures = []
    failures += check_group(FROM_CHECKOUT, CODEX, 'from the checkout (tracked)')
    failures += check_group(
        FROM_CYCLE_BUILD, CODEX, 'from the checkout (built, not tracked)',
        hint='run cycle.sh once; it bundles the plug (the author\'s compile '
             'step stubbed) and compiles it through the seed')
    failures += check_group(FROM_LADDER, LADDER, 'from the ladder')

    left, bootstraps = check_leftovers()
    print(f'unconverted root derivations: {len(left)}')
    print(f'sanctioned bootstraps: {len(bootstraps)}')

    for line in check_table():
        print(f'\n{line.strip()}')

    if failures:
        print('\nUNRESOLVED PATHS:')
        print('\n'.join(failures))
    if left:
        print('\nSITES STILL COUNTING DIRECTORIES:')
        print('\n'.join(left))
    if bootstraps:
        print('\nBOOTSTRAPS (allowed; each reaches the ladder, none the checkout):')
        print('\n'.join(bootstraps))

    if failures or left:
        print('\nFAIL')
        return 1
    print('\nOK: every path resolves, and the checkout is reached only '
          'through ladder_root')
    return 0


if __name__ == '__main__':
    sys.exit(main())
