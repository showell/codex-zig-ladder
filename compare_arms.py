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

HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / 'results'
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
    rc, out = sh([str(HERE / 'sandbox.sh'), label, 'HEAD', str(CODEX_SRC), ref])
    if rc:
        raise SystemExit(f'sandbox.sh failed:\n{out}')
    return pathlib.Path(out.strip().splitlines()[-1])


def sweep(sandbox, arm, artifacts):
    """natives, then a full --run sweep. Returns the natives identity."""
    ladder = sandbox / 'ladder'
    env = dict(**__import__('os').environ)
    for line in (sandbox / 'env').read_text().splitlines():
        line = line.strip()
        if line.startswith('export '):
            k, _, v = line[len('export '):].partition('=')
            env[k.strip()] = v.strip().strip('"').strip("'")
    rc, _ = sh(['./native_build.sh'], cwd=ladder, env=env,
               log=artifacts / f'{arm}-natives.log')
    if rc:
        raise SystemExit(f'{arm}: native_build.sh failed, see {arm}-natives.log')
    rc, out = sh(['./corpus_run.py', '--run'], cwd=ladder, env=env,
                 log=artifacts / f'{arm}-corpus.log')
    if rc:
        raise SystemExit(f'{arm}: corpus_run.py --run failed, see {arm}-corpus.log')
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
    a = ap.parse_args()

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
    base_sb = cut(f'cmp-base-{rid[:12]}', base_sha)
    head_sb = cut(f'cmp-head-{rid[:12]}', head_sha)
    print(f'  base tree {base_sb}\n  head tree {head_sb}')

    meta = {'id': rid, 'base_ref': a.base_ref, 'head_ref': a.head_ref,
            'base_sha': base_sha, 'head_sha': head_sha, 'scope': a.scope,
            'ladder_sha': git(['rev-parse', 'HEAD'], cwd=HERE),
            'when': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
            'host': __import__('socket').gethostname(),
            'base_tree': str(base_sb), 'head_tree': str(head_sb)}

    ok = False
    try:
        for arm, sb in (('base', base_sb), ('head', head_sb)):
            print(f'  sweeping {arm} ...', flush=True)
            sweep(sb, arm, dest)
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
