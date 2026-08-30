#!/usr/bin/env python3
"""One command for a before-and-after: cut both trees, sweep both, write ONE result.

    ./compare_arms.py <base-ref> <head-ref> [--scope derived|all] [--keep]

THIS REPLACES A HAND-WRITTEN SCRIPT PAIR PER CHANGE. There were three --
`dup.sh`/`dup_baseline.sh`, `bitcast.sh`/`bitcast_baseline.sh`, and a one-off for
the arc tangent -- each 40 to 120 lines of bash re-deriving the same shape, each
written under time pressure, and each buggy. On 2026-08-30 alone: a shell syntax
error that killed a run after its useful work, an integer comparison against a
two-line string that reported a passing check as failed, and a hard-coded
sandbox path that was wrong the moment sandbox.sh chose a different timestamp.
None of those were measurement defects. All three were scaffolding.

WHAT A RUN PRODUCES IS A FILE, AND THE FILE IS THE DELIVERABLE. Before this, a
finished comparison left a log inside a directory the checklist says to delete,
and the numbers reached a PR body by being retyped -- twice on 2026-08-30, once
wrongly. `results/<id>/result.json` and `result.md` carry both tree shas, the
natives identity of each arm, the seed, the selection rule and its population,
and EVERY moved verdict and differing file by name. Small enough to commit,
which is the point: the sandboxes become genuinely disposable because the answer
no longer lives in them.

RUNS EXPIRE, RESULTS PERSIST. A sandbox is scratch with a lifetime in hours and
is retired here unless the run failed or --keep was passed. A result is a
committed artifact. We had this exactly backwards: 3.3 GB of trees kept, and the
verdicts living in prose.

IDENTITY IS CONTENT, NOT A TIMESTAMP. The run id is a hash of (base sha, head
sha, selection rule), so the same comparison is recognisably the same run and
re-running says so instead of quietly making a second copy under a new name.
"""
import argparse, hashlib, json, pathlib, shutil, subprocess, sys, datetime
from affected import changed_paths, classify, affected

HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / 'results'
SCOPE = ['core']            # set from --scope; a list so sweep() can read it
CODEX_SRC = pathlib.Path.home() / 'showell_repos' / 'NewRepository'


def sh(cmd, cwd=None, env=None, log=None):
    """Run, stream nothing, return (rc, output). Every caller checks rc."""
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    out = p.stdout + p.stderr
    if log:
        pathlib.Path(log).write_text(out)
    return p.returncode, out


def git(args, cwd):
    rc, out = sh(['git'] + args, cwd=cwd)
    if rc:
        raise SystemExit(f'git {" ".join(args)} failed in {cwd}:\n{out}')
    return out.strip()


def resolve_ref(ref):
    return git(['rev-parse', ref], cwd=CODEX_SRC)


def run_id(base_sha, head_sha, scope):
    h = hashlib.sha256(f'{base_sha}\n{head_sha}\n{scope}'.encode()).hexdigest()[:12]
    return f'{head_sha[:8]}-vs-{base_sha[:8]}-{scope}-{h}'


def cut(label, ref):
    """Cut a sandbox and RECOGNISE its path, rather than trusting a position.

    This took `out.strip().splitlines()[-1]`, which is wrong for a reason worth
    keeping: `sh` concatenates stdout and stderr, sandbox.sh writes the path to
    stdout and its human notes to stderr, so the last line was a note. The
    script then tried to open `'    (no natives, ...)/env'`. Parsing human
    output by position is a guess; checking that the thing you found is
    actually a sandbox is not.
    """
    rc, out = sh([str(HERE / 'sandbox.sh'), label, 'HEAD', str(CODEX_SRC), ref])
    if rc:
        raise SystemExit(f'sandbox.sh failed:\n{out}')
    found = [pathlib.Path(l.strip()) for l in out.splitlines() if l.strip().startswith('/')]
    for cand in reversed(found):
        if (cand / 'ladder').is_dir() and (cand / 'env').is_file():
            return cand
    raise SystemExit(f'sandbox.sh printed no path holding ladder/ and env:\n{out}')


def arm_env(sandbox):
    """SOURCE the sandbox's env file. Do not parse it.

    It is a shell script, not a list of assignments: it sources
    `~/.codex_ladder_env` inside a conditional, and that host file is where
    CODEX_LADDER_VENUE lives -- which every compute entry point refuses to run
    without. A regex over lines beginning with `export ` collected CODEX_ROOT
    and SANDBOX, missed the venue entirely, and the refusal that followed said
    neither "error" nor "SIZE" so `ringplug_build.sh`'s `grep | head` swallowed
    it and printed a bare PLUG COMPILE FAILED. Twelve minutes to find, on a
    build that works perfectly when run by hand.
    """
    out = subprocess.run(
        ['bash', '-c', f'set -a; . {sandbox}/env >/dev/null 2>&1; env -0'],
        capture_output=True)
    env = {}
    for item in out.stdout.decode('utf-8', 'replace').split('\0'):
        if '=' in item:
            k, _, v = item.partition('=')
            env[k] = v
    if 'CODEX_LADDER_VENUE' not in env:
        raise SystemExit(f'{sandbox}/env yielded no CODEX_LADDER_VENUE; '
                         'every compute entry point refuses without it')
    if not env.get('CODEX_ROOT', '').startswith(str(sandbox)):
        raise SystemExit(f'CODEX_ROOT is {env.get("CODEX_ROOT")!r}, not inside '
                         f'{sandbox} -- the sandbox would be decoration')
    return env


def build_and_transpile(sandbox, arm, artifacts):
    """Natives, then transpile the WHOLE population. The cheap half.

    Native-only, no QEMU and no zig compilation, so this is minutes for the
    entire corpus -- and it computes a `zig_sha` per program, which is the
    number that decides what the expensive half has to touch.
    """
    ladder = sandbox / 'ladder'
    env = arm_env(sandbox)
    rc, _ = sh(['./native_build.sh'], cwd=ladder, env=env,
               log=artifacts / f'{arm}-natives.log')
    if rc:
        raise SystemExit(f'{arm}: native_build.sh failed, see {arm}-natives.log')
    rc, out = sh(['./corpus_run.py', '--transpile', '--scope', SCOPE[0]],
                 cwd=ladder, env=env, log=artifacts / f'{arm}-transpile.log')
    if rc:
        raise SystemExit(f'{arm}: --transpile failed, see {arm}-transpile.log')
    return out


def differing_names(base_sb, head_sb):
    """Programs whose emitted zig is NOT byte-identical across the arms.

    Plus anything present on one arm only, which has no counterpart to be
    identical to and must therefore be run.
    """
    _, btr, _ = load_arm(base_sb)
    _, ftr, _ = load_arm(head_sb)
    names = set()
    for n in set(btr) | set(ftr):
        b, f = btr.get(n), ftr.get(n)
        if b is None or f is None:
            names.add(n); continue
        if b.get('zig_sha') != f.get('zig_sha'):
            names.add(n)
    return sorted(names), len(set(btr) | set(ftr))


def run_subset(sandbox, arm, artifacts, names):
    """The expensive half, over the differing set only."""
    ladder = sandbox / 'ladder'
    sel = ladder / 'corpus' / 'to-run.txt'
    sel.parent.mkdir(exist_ok=True)
    sel.write_text('\n'.join(names) + ('\n' if names else ''))
    rc, out = sh(['./corpus_run.py', '--run', '--run-only', str(sel)],
                 cwd=ladder, env=arm_env(sandbox),
                 log=artifacts / f'{arm}-corpus.log')
    if rc:
        raise SystemExit(f'{arm}: --run failed, see {arm}-corpus.log')
    return out


def load_arm(sandbox):
    work = sandbox / 'ladder' / 'corpus'
    tr = {r['name']: r for r in json.loads((work / 'transpile.json').read_text())}
    vd = {}
    jl = work / 'run.jsonl'
    if jl.is_file():
        for line in jl.read_text().splitlines():
            if line.strip():
                e = json.loads(line)
                vd[e['name']] = e.get('verdict', '?')
    return work, tr, vd


def compare(base_sb, head_sb):
    """Every difference, by name. Nothing is truncated: a report that samples
    is how a sweep that touched nothing got read as a sweep that found nothing."""
    bw, btr, bvd = load_arm(base_sb)
    fw, ftr, fvd = load_arm(head_sb)
    out = {
        'population': {'base': len(btr), 'head': len(ftr),
                       'only_base': sorted(set(btr) - set(ftr)),
                       'only_head': sorted(set(ftr) - set(btr))},
        'stages': {'base': _hist(btr), 'head': _hist(ftr)},
        'verdict_moves': [], 'zig_differs': [], 'zig_same': 0,
    }
    for n in sorted(set(btr) & set(ftr)):
        b, f = btr[n], ftr[n]
        if b.get('stage') != f.get('stage'):
            out.setdefault('stage_moves', []).append(
                {'name': n, 'base': b.get('stage'), 'head': f.get('stage')})
        if n in bvd and n in fvd and bvd[n] != fvd[n]:
            out['verdict_moves'].append({'name': n, 'base': bvd[n], 'head': fvd[n]})
        bs, fs = b.get('zig_sha'), f.get('zig_sha')
        if bs and fs:
            if bs == fs:
                out['zig_same'] += 1
            else:
                bz, fz = bw / f'{n}.zig', fw / f'{n}.zig'
                delta = None
                if bz.is_file() and fz.is_file():
                    bl, fl = bz.read_text().splitlines(), fz.read_text().splitlines()
                    delta = {'base_lines': len(bl), 'head_lines': len(fl)}
                out['zig_differs'].append({'name': n, **(delta or {})})
    out.setdefault('stage_moves', [])
    return out


def _hist(tr):
    import collections
    return dict(collections.Counter(r.get('stage') for r in tr.values()))


def render(meta, cmp_):
    L = [f"# {meta['id']}", '',
         f"**{meta['head_ref']}** (`{meta['head_sha'][:8]}`) against "
         f"**{meta['base_ref']}** (`{meta['base_sha'][:8]}`)", '',
         f"Run {meta['when']} on {meta['host']}. Ladder `{meta['ladder_sha'][:8]}`. "
         f"Scope `{meta['scope']}`.", '',
         '## The one line', '',
         f"stage moves {len(cmp_['stage_moves'])}, verdict moves "
         f"{len(cmp_['verdict_moves'])}, zig differs {len(cmp_['zig_differs'])} "
         f"of {len(cmp_['zig_differs']) + cmp_['zig_same']}", '',
         '## What was run, and what was not', '',
         f"Emitted zig differed for **{meta['run_selection']['differing']}** of "
         f"{meta['run_selection']['population']} programs. Only those were built "
         f"and executed. The other {meta['run_selection']['skipped']} emitted "
         f"byte-identical zig on both arms, so with the same zig version they "
         f"produce the same binary and cannot have moved -- not run, and not "
         f"evidence of anything either.", '',
         '## Population', '',
         f"base {cmp_['population']['base']}, head {cmp_['population']['head']}"]
    for side in ('only_base', 'only_head'):
        v = cmp_['population'][side]
        if v:
            L += ['', f'**{side}** ({len(v)}): ' + ', '.join(v)]
    L += ['', '## Stages', '', '| stage | base | head |', '|---|---|---|']
    for s in sorted(set(cmp_['stages']['base']) | set(cmp_['stages']['head'])):
        L.append(f"| {s} | {cmp_['stages']['base'].get(s,0)} | {cmp_['stages']['head'].get(s,0)} |")
    for key, title in (('stage_moves', 'Stage moves'),
                       ('verdict_moves', 'Verdict moves'),
                       ('zig_differs', 'Emitted zig differs')):
        rows = cmp_[key]
        L += ['', f'## {title} ({len(rows)})']
        if not rows:
            L += ['', 'none']
            continue
        L.append('')
        for r in rows:
            bits = ', '.join(f'{k} {v}' for k, v in r.items() if k != 'name')
            L.append(f"- `{r['name']}`" + (f' — {bits}' if bits else ''))
    return '\n'.join(L) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('base_ref')
    ap.add_argument('head_ref')
    ap.add_argument('--scope', default='all')
    ap.add_argument('--keep', action='store_true',
                    help='do not retire the sandboxes (needs a reason in the result)')
    ap.add_argument('--plan', action='store_true',
                    help='say what this run would do and stop. Two seconds.')
    a = ap.parse_args()
    SCOPE[0] = a.scope if a.scope in ('core', 'all') else 'core'

    base_sha, head_sha = resolve_ref(a.base_ref), resolve_ref(a.head_ref)
    rid = run_id(base_sha, head_sha, a.scope)
    dest = RESULTS / rid
    if dest.exists():
        raise SystemExit(f'{rid} already exists -- that comparison has been run.\n'
                         f'  {dest}\nDelete it to redo, or change the scope.')
    dest.mkdir(parents=True)

    print(f'run {rid}')
    print(f'  base {a.base_ref} {base_sha[:8]}')
    print(f'  head {a.head_ref} {head_sha[:8]}')

    # THE CHEAPEST GUARD THERE IS. A 150-minute run that is wrong costs 300
    # minutes, because you run it again -- so the number worth reducing is the
    # chance of being wrong, not the duration. On 2026-08-30 a 28-minute sweep
    # measured a chapter that nothing in the corpus cites; the question that
    # would have caught it takes one second to ask and nobody asked it.
    changed = changed_paths(base_sha, head_sha, CODEX_SRC)
    scope_kind, detail = classify(changed)
    hits = []
    print(f'\n  {len(changed)} file(s) changed')
    if scope_kind == 'all':
        print('  blast radius: EVERY program -- these paths decide all emission:')
        for q in detail:
            print(f'      {q}')
    else:
        hits = affected(detail['chapters'], set(detail['tests']),
                        head_sha, CODEX_SRC)
        print(f"  blast radius: {len(hits)} program(s) can see this change")
        for rel, why in hits:
            print(f'      {rel[len("codex/test/"):]}   ({why})')
        if not hits:
            print('\n  REFUSING: nothing in the corpus can see this change.')
            print('  A sweep would come back clean and mean nothing. Use '
                  'bare_expected.py on the cited chapter\'s own consumers.')
            return 1
    # SCOPE AND RELEVANCE ARE DIFFERENT AXES, and conflating them is how a
    # cheap sweep repeats an expensive sweep's mistake. Scope sets baseline
    # BREADTH and is chosen on cost; the affected set is chosen on CORRECTNESS
    # and goes in whatever it costs. Measured 2026-08-30: scope `core` holds
    # every test our outbound PRs add, and still misses 3 of the 5 programs
    # that can see the arc tangent, all in the expensive apps/ quarter. Those
    # three cost about fifteen seconds and are 60% of that change's coverage.
    forced = sorted(r[len('codex/test/'):] for r, _ in hits) if scope_kind != 'all' else []
    if forced:
        print(f'  forced into the sweep regardless of scope: {len(forced)}')
    if a.plan:
        print(f'\n  would write {dest}')
        print('  --plan: stopping before any box time is spent')
        dest.rmdir()
        return 0

    base_sb = cut(f'cmp-base-{rid[:12]}', base_sha)
    head_sb = cut(f'cmp-head-{rid[:12]}', head_sha)
    print(f'  base tree {base_sb}\n  head tree {head_sb}')

    meta = {'id': rid, 'base_ref': a.base_ref, 'head_ref': a.head_ref,
            'base_sha': base_sha, 'head_sha': head_sha, 'scope': a.scope,
            'ladder_sha': git(['rev-parse', 'HEAD'], cwd=HERE),
            'when': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
            'host': __import__('socket').gethostname(),
            'base_tree': str(base_sb), 'head_tree': str(head_sb),
            'forced': forced}

    ok = False
    try:
        for arm, sb in (('base', base_sb), ('head', head_sb)):
            print(f'  [1/3] natives + transpile, {arm} ...', flush=True)
            build_and_transpile(sb, arm, dest)

        # WHICH ARM ARE YOU STANDING ON. The two arms must not share natives.
        # A comparison whose arms were built from the same tree reports perfect
        # agreement and means nothing, and nothing about the output would say
        # so. Cheap, total, and checked rather than trusted.
        import hashlib as _h
        def _sha(f):
            return _h.sha256(f.read_bytes()).hexdigest()[:16] if f.is_file() else None
        same = []
        for tool in ('native/zigemit', 'native/codexir'):
            b, f = base_sb / 'ladder' / tool, head_sb / 'ladder' / tool
            sb_, sf = _sha(b), _sha(f)
            meta.setdefault('natives', {}).setdefault(tool, {})['base'] = sb_
            meta['natives'][tool]['head'] = sf
            if sb_ is not None and sb_ == sf:
                same.append(tool)
        if same and any(q.startswith(('codex/plugs/', 'codex/compiler/')) for q in changed):
            raise SystemExit(
                'ARMS SHARE NATIVES: ' + ', '.join(same) + ' are byte-identical '
                'across the two trees, but this change touches the plug or the '
                'compiler. Either the sandboxes were built from the same tree or '
                'the build did not rerun. The comparison would be meaningless.')

        names, total = differing_names(base_sb, head_sb)
        meta['run_selection'] = {'differing': len(names), 'population': total,
                                 'skipped': total - len(names), 'names': names}
        print(f'  [2/3] byte-diff: {len(names)} of {total} programs differ; '
              f'{total - len(names)} cannot have moved and will not be run')
        for arm, sb in (('base', base_sb), ('head', head_sb)):
            print(f'  [3/3] running {len(names)} on {arm} ...', flush=True)
            run_subset(sb, arm, dest, names)

        cmp_ = compare(base_sb, head_sb)
        (dest / 'result.json').write_text(json.dumps({'meta': meta, 'compare': cmp_}, indent=1))
        (dest / 'result.md').write_text(render(meta, cmp_))
        print('\n' + render(meta, cmp_).split('## Population')[0])
        print(f'result: {dest}/result.md')
        ok = True
    finally:
        if ok and not a.keep:
            for sb in (base_sb, head_sb):
                shutil.rmtree(sb, ignore_errors=True)
            print('sandboxes retired')
        elif not ok:
            print(f'FAILED -- sandboxes kept for debugging:\n  {base_sb}\n  {head_sb}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
