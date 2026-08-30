#!/usr/bin/env python3
"""Run the depot's own test battery through the plug, natively.

`codex/test/` holds ~560 top-level Codex programs (566 at Update 47), most
beside a hand-verified `.expected` file. That is an oracle per program,
written by someone with no knowledge of this plug, which is the one property
our own probes can never have: a probe tests what we already suspect.

Two stages, cheap first, because they answer different questions.

  --transpile   .codex -> IR -> .zig for every program, and histogram the
                @compileError markers. No zig compilation at all, so this is
                minutes for the whole corpus. The output is a census of the
                emitter's coverage RANKED BY HOW OFTEN each gap actually bites,
                which is the number that says what to fix first.

  --run         for the programs that transpiled clean, build and run the zig
                and diff against `.expected`. Hours, unattended, and this is the
                conformance answer.

Both stages go through native/codexir and native/zigemit, so no QEMU is
involved. That is the whole reason this is affordable: the same questions asked
through the ladder would each cost a bundle, a seed compile and a plug boot.

The circularity is worth stating rather than hiding: codexir is the compiler AS
TRANSPILED BY THE PLUG under test, so this is the plug grading its own homework
at one remove. Fine for finding divergences, useless as a trust claim. Anything
this turns up gets confirmed against the seed before it is believed, exactly the
way the ladder banks.
"""

import argparse
import collections
import datetime
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
import compute_lock
import tool_identity
from cite_resolve import resolve
from ladder_root import CODEX, LADDER

TESTS = CODEX / 'codex' / 'test'
CODEXIR = LADDER / 'native' / 'codexir'
ZIGEMIT = LADDER / 'native' / 'zigemit'
WORK = LADDER / 'corpus'
CENSUS = WORK / 'census.json'
HW_ONLY_FILE = WORK / 'hardware-only.txt'
MARKER = re.compile(r'@compileError\("zig plug: ([^"]*)"\)')

# Prelude preconditions wear the same spelling as refusals and are not
# refusals; findings/prelude-comptime-guards.txt says which and why. Here the
# cost of confusing them is the highest of the three scans that read this
# list: one prelude guard marked EVERY program 'markers', which disqualified
# all of them from the --run stage, so a census that looked like it ran
# answered nothing -- and it read as a regression, `deck-bracket-contract`
# flipping match -> markers against the bank.
PRELUDE_GUARDS = frozenset(
    m.group(1)
    for ln in (LADDER / 'findings' / 'prelude-comptime-guards.txt')
    .read_text().splitlines()
    if ln.strip() and not ln.startswith('#')
    for m in [MARKER.search(ln)] if m
)


def expected_text(name):
    """The .expected content as the comparison sees it, or None. One home for
    the normalization: 76 of the depot's .expected files open with one 0x01
    the console capture wrote, and a subset of exactly those use CRLF --
    every CRLF file is 0x01-marked, no unmarked file holds a CR, and
    marked/unmarked siblings (vec-array vs vec-pattern) have identical prints
    and openings, so both bytes are the capture path's line discipline, not
    output. The depot's own adjudicator (build/test.ps1 phase 2) strips every
    CR the same way."""
    exp = TESTS / f'{name}.expected'
    if not exp.is_file():
        return None
    want = exp.read_text(errors='replace').replace('\r', '')
    return want[1:] if want.startswith('\x01') else want


def expected_sha(name):
    want = expected_text(name)
    return None if want is None else hashlib.sha256(
        want.strip().encode()).hexdigest()[:16]


def load_hardware_only():
    """name -> reason for programs whose expected output only real hardware
    can produce (secondary cores, devices). They classify instead of running:
    a hosted single process cannot answer them, so a crash or differ there is
    noise, and running them at all invites one (the smp-* pair peeks ~2.1 GB
    physical, which the contiguous heap model turns into an OOM). The class
    is loud everywhere it goes: its own verdict, its own tally line, banked
    in the census like any other verdict."""
    if not HW_ONLY_FILE.is_file():
        return {}
    hw = {}
    for line in HW_ONLY_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, _, reason = line.partition(' ')
        if not (TESTS / f'{name}.codex').is_file():
            raise SystemExit(f'{HW_ONLY_FILE.name}: {name} is not in the '
                             f'corpus; a stale exclusion must not linger')
        hw[name] = reason.strip()
    return hw


def need_tools():
    for t in (CODEXIR, ZIGEMIT):
        if not t.is_file():
            raise SystemExit(f'{t} missing; run native_build.sh (it needs QEMU once)')


def transpile(src, out_dir):
    """One program from Codex source to zig. Returns a verdict dict."""
    r = {'name': src.stem}
    # Resolve cites first. A test is usually a driver and the function it calls
    # lives in a cited chapter; codexir resolves nothing, so without this the
    # call arrives as an undefined name and the plug's fallback fires, which
    # looks exactly like an emitter gap and is not one.
    unit, missing = resolve(src)
    if missing:
        r['stage'] = 'unresolved'
        r['detail'] = '; '.join(f'{q} chapter {n}' for _, q, n in missing[:3])
        return r
    ir = subprocess.run([str(CODEXIR)], input=unit.encode(),
                        capture_output=True, timeout=120)
    # Output lands on stderr because print-text is std.debug.print in the
    # emitted runtime. That is a wart the plug should fix, not a design.
    if ir.returncode != 0 or not ir.stderr:
        r['stage'] = 'codexir'
        r['detail'] = f'rc={ir.returncode} signal={-ir.returncode if ir.returncode < 0 else 0}'
        return r
    # THE DRIVER'S ERROR GATE. A refused compile exits 0 and writes
    # `CODEGEN-HALTED: ... no IR emitted` where the IR would go, so the two
    # checks above pass it through and zigemit is handed a diagnostic to parse
    # as a wire. It fails, and the program is recorded against the EMITTER.
    # On 2026-08-27 all 13 programs in the `zigemit` bucket were this: not one
    # was an emitter failure, and several are deliberate negative tests the
    # census has no way to expect. codexzig_corpus.py has checked for this
    # line since it was written; this runner never did.
    halted = next((l for l in ir.stderr.decode('utf-8', 'replace').splitlines()
                   if l.startswith('CODEGEN-HALTED')), None)
    if halted:
        r['stage'] = 'codex-refused'
        r['detail'] = halted[:160]
        return r
    (out_dir / f'{src.stem}.ir').write_bytes(ir.stderr)

    zg = subprocess.run([str(ZIGEMIT)], input=ir.stderr,
                        capture_output=True, timeout=120)
    if zg.returncode != 0 or not zg.stderr:
        r['stage'] = 'zigemit'
        r['detail'] = f'rc={zg.returncode}'
        return r
    zig = zg.stderr.decode('utf-8', 'replace')
    (out_dir / f'{src.stem}.zig').write_text(zig)
    # A program's verdict is a pure function of (this file) x (zig toolchain),
    # so the hash is the cache key --changed compares against the bank.
    r['zig_sha'] = hashlib.sha256(zig.encode()).hexdigest()[:16]

    marks = [m for m in MARKER.findall(zig) if m not in PRELUDE_GUARDS]
    r['stage'] = 'markers' if marks else 'clean'
    r['markers'] = marks
    return r


def select_population(tests):
    """Every Codex program under `codex/test/`, recursively.

    THIS WAS `tests.glob('*.codex')` -- NON-RECURSIVE -- UNTIL 2026-08-30, and
    the comment defending it said "codexir resolves no cites, so ... until there
    is a resolver, the honest corpus is the self-contained programs." There has
    been a resolver for some time: this file imports it at the top and calls it
    in `transpile`, and the `--all` flag's own help text says "cites are
    resolved now, so every program is in scope". The glob outlived all three
    facts.

    What it cost: 614 of 1,701 programs swept. Everything under `ops/` was
    excluded -- which is where OUR OWN PR EVIDENCE LIVES. `real-bitcast-f64`,
    `real-int-conversions` and `real-saturating-finite`, the tests written to
    demonstrate PRs 100 and 105 and the control cited in every PR body as proof
    the rig is not fooling itself, have never once been in this corpus.

    NO DIRECTORY IS EXCLUDED, deliberately, including `errors/`. A two-arm
    comparison measures MOVEMENT, not absolute pass or fail: a program that
    refuses on both arms costs a cheap transpile and contributes nothing, while
    a program whose refusal STOPS is a regression worth catching. Excluding a
    directory on a guess about what it can tell us is the exact move that
    produced the 614.

    A stem must be unique across the whole tree, because every artifact this
    corpus writes -- `transpile.json`, `run.jsonl`, `<name>.zig`, and both
    sides of `two_arm_diff.py` -- is keyed by bare name. A collision would
    silently pair one program's output with another's. Checked here rather than
    assumed, and loudly, because the failure is invisible.
    """
    names = sorted(tests.rglob('*.codex'))
    seen = {}
    dupes = []
    for n in names:
        if n.stem in seen:
            dupes.append((n.stem, seen[n.stem], n))
        seen[n.stem] = n
    if dupes:
        lines = '\n'.join(f'  {s}: {a.relative_to(tests)} and {b.relative_to(tests)}'
                           for s, a, b in dupes)
        raise SystemExit('corpus: stems must be unique, every artifact is keyed '
                         f'by bare name:\n{lines}')
    return names


def population_composition(tests, names):
    """Where the programs came from, by directory. One line, always printed.

    The count alone cannot say whether a directory was silently dropped; the
    breakdown can, and it is the line that would have made the 614 obvious
    years earlier than it became obvious.
    """
    by = collections.Counter(
        str(n.parent.relative_to(tests)) if n.parent != tests else '.'
        for n in names)
    return '  by directory: ' + ', '.join(
        f'{d} {c}' for d, c in sorted(by.items(), key=lambda kv: -kv[1]))


def population_provenance(tests):
    """Which git ref, if any, describes the set of programs about to be run.

    THE MANIFEST STAMPS THE CHECKOUT, NOT THE POPULATION, and those are not the
    same fact. On 2026-08-27 a sandbox was measured with 29 port files copied
    in untracked: 624 programs, a headline result quoted all evening, and no
    ref anywhere describes that tree. The MANIFEST said `codex-at-creation` and
    was perfectly correct and perfectly useless for reproducing it.

    So every run now says whether its population is a ref or a one-off. Cheap,
    printed next to the count it qualifies, and loud when it matters.
    """
    try:
        head = subprocess.run(['git', '-C', str(tests), 'rev-parse', '--short', 'HEAD'],
                              capture_output=True, text=True, timeout=15).stdout.strip()
        dirty = subprocess.run(['git', '-C', str(tests), 'status', '--porcelain', '.'],
                               capture_output=True, text=True, timeout=30).stdout.splitlines()
    except Exception as e:                       # not a checkout, or no git
        return f'  population: NOT UNDER GIT ({e.__class__.__name__}) -- not reproducible'
    if not head:
        return '  population: NOT UNDER GIT -- not reproducible'
    untracked = [l for l in dirty if l.startswith('??')]
    modified = [l for l in dirty if not l.startswith('??')]
    if not dirty:
        return f'  population: {head}, clean -- reproducible from that ref'
    bits = []
    if untracked: bits.append(f'{len(untracked)} untracked')
    if modified: bits.append(f'{len(modified)} modified')
    return (f'  population: {head} PLUS {", ".join(bits)} -- NO REF DESCRIBES THIS SET,\n'
            f'  so any number from this run is not reproducible from a commit')


def stage_transpile(names, out_dir):
    results, hist = [], collections.Counter()
    for i, src in enumerate(names, 1):
        try:
            r = transpile(src, out_dir)
        except subprocess.TimeoutExpired:
            r = {'name': src.stem, 'stage': 'timeout', 'detail': 'over 120s'}
        except Exception as e:                      # a crash here is data too
            r = {'name': src.stem, 'stage': 'error', 'detail': repr(e)[:120]}
        results.append(r)
        # Count PROGRAMS, not occurrences. A builtin used 76 times in one
        # program and one used once in 76 programs are very different facts,
        # and the second is the one that says what to implement first.
        for m in set(r.get('markers', ())):
            hist[m] += 1
        if i % 100 == 0:
            print(f'  {i}/{len(names)}', flush=True)

    by = collections.Counter(r['stage'] for r in results)
    print(f'\n{len(results)} programs: ' +
          ', '.join(f'{k} {v}' for k, v in by.most_common()))

    # The histogram is the point of this stage. A gap that bites 400 programs
    # and a gap that bites one are the same line of missing code and very
    # different priorities, and nothing else we have measures that.
    if hist:
        print(f'\nemitter gaps, by how many programs hit them '
              f'({len(hist)} distinct):')
        for name, n in hist.most_common(40):
            print(f'  {n:5d}  {name}')
    return results, hist


# A RESIDENT bound on each `zig run` and the program it executes. Emitted
# binaries have ballooned to 3 GB anon RSS, and on 2026-08-19 one such run
# livelocked the whole WSL VM instead of drawing a clean OOM kill. The old
# guard was RLIMIT_AS, which counts RESERVED address space -- and the
# heap-unification emitter reserves its arena (4 GiB, lazily faulted, ~145 MB
# resident on a typical program) up front, so an address-space cap refuses
# every legitimate program before it touches a page. cgroup MemoryMax counts
# what a runaway actually costs the box; 800 MB is the old cap's figure in
# the right unit (the full corpus replayed under it with zero hits and max RSS
# 145 MB). The kernel's kill is exit 137, read below as a crash. No fallback:
# the laptop is not a venue (compute_lock.require_venue).
RUN_MEMORY_MAX = '800M'
BOUNDED = ['systemd-run', '--user', '--scope', '-p', f'MemoryMax={RUN_MEMORY_MAX}', '--quiet']


def _require_bounded():
    if shutil.which('systemd-run') is None:
        raise SystemExit('corpus_run: no systemd-run on this host -- the resident '
                         'bound is not optional; refusing')


def load_run_carry(results):
    """Verdicts from an earlier interrupted or batched --run that still hold.

    A verdict is a pure function of (its emitted zig) x (zig toolchain) x (the
    .expected it was diffed against), so EVERY PART OF THAT KEY IS WRITTEN ON
    THE VERDICT'S OWN LINE. The check is against the line, never against a
    second file.

    It used to read the shas from `transpile.json`, captured before this
    invocation overwrote it. That baseline is forgeable: a bare `--transpile`
    also writes that file, so `./corpus_run.py --transpile` followed by
    `./corpus_run.py --run` made prev == now for every program and carried the
    whole journal unconditionally. On 2026-08-27 that reported 94 programs as
    `match -> refused` against a compiler change that had left 570 of 577
    emitted files byte-identical. A line missing its key does not carry.
    """
    jsonl = WORK / 'run.jsonl'
    if not jsonl.is_file():
        return {}
    lines = []
    raw = jsonl.read_text().splitlines()
    for i, l in enumerate(raw):
        try:
            lines.append(json.loads(l))
        except json.JSONDecodeError:
            if i == len(raw) - 1:
                print(f'  dropping torn final line of {jsonl}')
                continue
            raise SystemExit(f'{jsonl} line {i + 1} is corrupt; inspect it')
    zv = zig_version()
    now = {r['name']: r.get('zig_sha') for r in results}
    carry, dropped, keyless = {}, 0, 0
    for e in lines:
        n = e['name']
        if e.get('zig_sha') is None:
            keyless += 1
            continue
        if (e['zig_sha'] == now.get(n)
                and e.get('expected_sha') == expected_sha(n)
                and e.get('zig') == zv):
            carry[n] = e
        else:
            dropped += 1
    print(f'\nresume: {len(carry)} verdicts carried from run.jsonl '
          f'(zig byte-identical, .expected unmoved, toolchain unmoved)'
          + (f'; {dropped} dropped as stale' if dropped else '')
          + (f'; {keyless} dropped as keyless (written before the key was '
             f'on the line)' if keyless else ''))
    return carry


def stage_run(results, out_dir, persist=True, batch=0, prior=None, hw=None):
    """Build and run what transpiled clean, diff against the depot's .expected."""
    hw = hw or {}
    # A hardware-only name never carries an old verdict: its classification
    # is this run's to make, even when a stale 'crashed' sits in run.jsonl.
    prior = {n: e for n, e in (prior or {}).items() if n not in hw}
    clean = [r for r in results if r['stage'] == 'clean']
    todo = [r for r in clean if r['name'] not in prior]
    if batch and batch < len(todo):
        print(f'\nbatch: running {batch} of {len(todo)} outstanding; '
              f'{len(todo) - batch} left for the next invocation')
        todo = todo[:batch]
    print(f'\n{len(clean)} clean programs; building and running {len(todo)}')
    tally = collections.Counter()
    detail = []
    verdicts = {}
    # One line per verdict, flushed as it lands: run.json at the end of the
    # loop kept nothing when the 2026-08-19 run died at program 101 of 250.
    # Carried lines are rewritten first, so the file is always exactly the
    # currently-valid verdict set -- stale lines do not linger.
    jsonl = (out_dir / 'run.jsonl').open('w') if persist else None
    zv = zig_version()
    for e in prior.values():
        tally[e['verdict']] += 1
        verdicts[e['name']] = (e['verdict'], e.get('detail', ''))
        if jsonl:
            jsonl.write(json.dumps(e) + '\n')
    if jsonl:
        jsonl.flush()

    sha_of = {r['name']: r.get('zig_sha') for r in results}

    def verdict(name, kind, note=''):
        tally[kind] += 1
        verdicts[name] = (kind, note)
        if kind not in ('match', 'no-expected', 'hardware-only'):
            detail.append((name, kind, note))
        if jsonl:
            # The verdict's cache key travels WITH it. A resume that has to
            # consult a second file to decide whether this line still holds is
            # a resume that can be lied to.
            jsonl.write(json.dumps({'name': name, 'verdict': kind,
                                    'detail': note, 'zig': zv,
                                    'zig_sha': sha_of.get(name),
                                    'expected_sha': expected_sha(name)}) + '\n')
            jsonl.flush()

    for i, r in enumerate(todo, 1):
        name = r['name']
        if name in hw:
            verdict(name, 'hardware-only', hw[name])
            continue
        exp = TESTS / f'{name}.expected'
        zig = out_dir / f'{name}.zig'
        if not exp.is_file():
            verdict(name, 'no-expected')
            continue
        try:
            p = subprocess.run(BOUNDED + ['timeout', '300', 'zig', 'run', str(zig)],
                               capture_output=True, timeout=330)
        except subprocess.TimeoutExpired:
            verdict(name, 'timeout')
            continue
        if p.returncode != 0:
            # A zig compile error here is a real finding: the plug emitted
            # something it believed in and zig refused it. A panic is a
            # different finding: zig accepted it and the program died running.
            stderr = p.stderr.decode('utf-8', 'replace')
            if p.returncode in (137, -9) or 'Killed' in stderr[-200:]:
                # The resident bound fired (cgroup OOM kill): its own verdict,
                # not a refusal, because nothing about the plug's output was
                # judged -- the program ate more than RUN_MEMORY_MAX.
                verdict(name, 'oom-killed', f'resident bound {RUN_MEMORY_MAX}')
                continue
            kind = 'crashed' if 'panic:' in stderr else 'refused'
            first = next((l for l in stderr.splitlines()
                          if 'error:' in l or 'panic:' in l), '')
            verdict(name, kind, first[:160])
            continue
        got = p.stderr.decode('utf-8', 'replace')
        want = expected_text(name)
        if got.strip() == want.strip():
            verdict(name, 'match')
        else:
            verdict(name, 'differ', f'want {want.strip()[:60]!r} got {got.strip()[:60]!r}')
        if i % 25 == 0:
            print(f'  {i}/{len(todo)}  {dict(tally)}', flush=True)

    if jsonl:
        jsonl.close()
    print('\n' + ', '.join(f'{k} {v}' for k, v in tally.most_common()))
    return tally, detail, verdicts


# The banked census: name -> {stage, zig_sha, markers, verdict}, written only
# by --bank and diffed like a truth file. Day to day the interesting output is
# the DIFF against it -- which programs flipped match->differ (a regression),
# differ->match (a fix landed), refused->match -- not the wholesale tally.
# The design behind it: corpus/README.md.

def load_bank():
    return json.loads(CENSUS.read_text()) if CENSUS.is_file() else None


def current_tools():
    """What the natives this invocation runs were BUILT FROM.

    Not their binary shas. Zig bakes the build directory into every binary,
    and every ladder run is a fresh sandbox, so binary shas differ on every
    run whatever the source did -- which made this function's answer, and
    therefore the staleness banner below, a constant. tool_identity derives
    the answer from the four inputs that decide the binary instead. See its
    module docstring for the incident.
    """
    return tool_identity.natives()


def current_base():
    """WHICH TREES produced this run, in terms a human can act on.

    A native's sha says two runs used different binaries. It cannot say what
    those binaries were built FROM, and the difference between "a release" and
    "a branch with unlanded work on it" is the whole question when a verdict
    moves. `truth/uNN/` has recorded the seed and the harness content per rung
    since 2026-08-25; the census recorded neither, so a bank could say the
    tools differed and never that the baseline was a branch.

    A detached worktree has no branch name and says so, rather than guessing.
    This docstring claimed that before the code did it: `rev-parse
    --abbrev-ref HEAD` answers the literal string "HEAD" when detached, and
    every ladder run is detached, so the field read like a branch named HEAD
    on every bank ever taken. `symbolic-ref --quiet` declines instead, which
    is the honest None.

    None on its own would make the field useless, though, because detached is
    the NORMAL case here -- so `codex_points_at` carries the names that do
    resolve this commit: branches, remote-tracking refs and tags alike. That
    is what answers the question the field exists for. A row reading
    `upstream/master` is a release; a row reading only a local branch name is
    unlanded work; an empty list is a commit nothing points at any more, which
    is worth knowing before trusting the bank.
    """
    def git(root, *args):
        try:
            r = subprocess.run(['git', '-C', str(root), *args],
                               capture_output=True, text=True, timeout=10)
            return r.stdout.strip() or None
        except Exception:
            return None
    def points_at(root):
        out = git(root, 'for-each-ref', '--points-at', 'HEAD',
                  '--format=%(refname:short)')
        return sorted(out.split('\n')) if out else []
    seed = CODEX / 'seed' / 'Codex.cdx'
    return {
        'codex': git(CODEX, 'rev-parse', 'HEAD'),
        'codex_branch': git(CODEX, 'symbolic-ref', '--quiet', '--short', 'HEAD'),
        'codex_points_at': points_at(CODEX),
        'ladder': git(LADDER, 'rev-parse', 'HEAD'),
        'seed': hashlib.sha256(seed.read_bytes()).hexdigest()[:16] if seed.is_file() else None,
    }


def bank_describes_this_tree(bank):
    """Whether the bank was taken with the tools now in `native/`.

    A diff against a bank taken with DIFFERENT tools is a diff between two
    measurements, not a report about a change -- and it reads identically to
    the real thing unless something says so. Saying so is this function.

    Three answers, not two. UNKNOWABLE is for a bank from before 2026-08-29,
    whose `tools` field holds binary shas: those are not comparable to
    anything, here or in the bank, so the honest report is that the question
    cannot be asked of it rather than a diff of two incomparable numbers. It
    is also the answer when this tree has not been bundled and the
    fingerprints come back None.
    """
    meta = bank.get('meta') or {}
    want = meta.get('built_from')
    if want is None:
        return 'unknowable', meta.get('tools') or {}
    now = current_tools()
    if any(v is None for v in now.values()):
        return 'unknowable', want
    return ('same' if want == now else 'different'), want


def write_bank(programs):
    meta = {
        'date': datetime.date.today().isoformat(),
        'zig': zig_version(),
        'built_from': current_tools(),
        'base': current_base(),
    }
    CENSUS.write_text(json.dumps({'meta': meta, 'programs': programs},
                                 indent=1, sort_keys=True))


def zig_version():
    return subprocess.run(['zig', 'version'], capture_output=True,
                          text=True).stdout.strip()


def census_key(entry):
    """The one word a program's row answers with: its run verdict when it has
    one, its transpile stage when it never ran."""
    return entry.get('verdict') or entry['stage']


def assemble_census(results, carried, verdicts):
    programs = {}
    for r in results:
        e = {'stage': r['stage']}
        if r.get('zig_sha'):
            e['zig_sha'] = r['zig_sha']
        marks = sorted(set(r.get('markers') or ()))
        if marks:
            e['markers'] = marks
        n = r['name']
        esha = expected_sha(n)
        if esha:
            e['expected_sha'] = esha
        if n in carried:
            e['verdict'] = carried[n]['verdict']
        elif n in verdicts:
            e['verdict'] = verdicts[n][0]
        programs[n] = e
    return programs


def print_bank_diff(bank, programs):
    # WHICH TREE IS THIS BANK ABOUT. A verdict diff is only a statement about
    # a change when both sides came from the same natives; otherwise it is two
    # unrelated measurements subtracted from each other, which is exactly how
    # 94 phantom regressions got reported on 2026-08-27. Loud, and before the
    # rows, because the rows are what gets read.
    verdict, want = bank_describes_this_tree(bank)
    if verdict != 'same':
        now = current_tools()
        if verdict == 'unknowable':
            print('\n*** THIS BANK CANNOT SAY WHICH TREE IT IS ABOUT ***')
            print('      It records `tools` as BINARY shas, which is what banks')
            print('      held before 2026-08-29. A binary carries its own build')
            print('      directory, so those numbers are not comparable to this')
            print('      tree or to each other. Re-bank to get an answer at all.')
            for t in sorted(want):
                print(f'      {t:9s} bank {want[t]} (a binary sha, incomparable)')
        else:
            print('\n*** THE BANK IS NOT ABOUT THIS TREE ***')
            for t in sorted(set(want) | set(now)):
                mark = '  ' if want.get(t) == now.get(t) else '<-'
                print(f'      {t:9s} bank {want.get(t, "(absent)")}  '
                      f'now {now.get(t, "(absent)")} {mark}')
        # The fingerprints say the tools were built from different sources.
        # They cannot say whether the bank came from a RELEASE or from a branch
        # carrying unlanded work, and that is the difference between "my change
        # moved this" and "the base did".
        was, isnow = (bank.get('meta') or {}).get('base'), current_base()
        if was:
            def norm(v):
                # "HEAD" is what banks before 2026-08-29 recorded for a
                # DETACHED worktree, which is every one of them, and None is
                # how the same fact is spelled now. Comparing the spellings
                # would report a move where nothing moved -- the original
                # mistake repeated at the reading end.
                return None if v == 'HEAD' else v

            def show(k, v):
                if isinstance(v, list):
                    return ', '.join(v) or '(nothing points at it)'
                if v is None:
                    return '(no branch: detached)'
                return v[:12] if k in ('codex', 'ladder') else v

            for k in ('codex', 'codex_branch', 'codex_points_at', 'ladder', 'seed'):
                if k == 'codex_points_at' and k not in was:
                    continue        # the bank predates the field; not a move
                a, b = norm(was.get(k)), norm(isnow.get(k))
                if a != b:
                    print(f'      {k:16s} bank {show(k, a):<26} '
                          f'now {show(k, b):<26} <-')
        else:
            print('      base      bank RECORDED NO BASE -- taken before this was')
            print('                written down, so which tree it measured is')
            at = ', '.join(isnow.get('codex_points_at') or []) or 'no named ref'
            print(f'                unknowable. This run is {(isnow.get("codex") or "?")[:12]}'
                  f' ({at}).')
        print('    Every row below is a difference between two measurements,')
        print('    not a change this run caused. Re-bank, or read it as such.')
    old = bank['programs']
    flips = []
    for n, e in programs.items():
        o = old.get(n)
        if o is None:
            flips.append((n, '(new)', census_key(e)))
        elif census_key(o) != census_key(e):
            flips.append((n, census_key(o), census_key(e)))
    if flips:
        print(f'\nverdict diff vs bank {bank["meta"]["date"]} ({len(flips)} moved):')
        for n, was, now in sorted(flips):
            print(f'  {n:36s} {was} -> {now}')
    else:
        print(f'\nno verdict moved vs bank {bank["meta"]["date"]}')
    gone = [n for n in old if n not in programs]
    if gone:
        print(f'  ({len(gone)} banked programs no longer in the corpus)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--transpile', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--changed', action='store_true',
                    help='re-emit everything, run only programs whose emitted '
                         'zig moved since the bank, report the verdict diff')
    ap.add_argument('--bank', action='store_true',
                    help='after a full --run or --changed: write census.json')
    ap.add_argument('--limit', type=int, default=0, help='first N programs only')
    ap.add_argument('--only', default='', metavar='NAMES',
                    help='comma-separated program names, for a covering set '
                         'rather than a prefix (census_canary.sh passes these)')
    ap.add_argument('--batch', type=int, default=0,
                    help='with --run: build/run at most N outstanding programs, '
                         'carrying earlier verdicts whose emitted zig is '
                         'byte-identical; rerun to continue where it left off')
    ap.add_argument('--all', action='store_true', help='(kept for the runner scripts; '
                    'cites are resolved now, so every program is in scope)')
    a = ap.parse_args()
    if not (a.transpile or a.run or a.changed):
        a.transpile = True
    if a.limit and (a.changed or a.bank):
        raise SystemExit('--changed and --bank are full-corpus operations; drop --limit')
    if a.only and (a.changed or a.bank):
        raise SystemExit('--changed and --bank are full-corpus operations; drop --only')
    if a.only and a.limit:
        raise SystemExit('--only and --limit both slice the corpus; pick one')
    if a.batch and not a.run:
        raise SystemExit('--batch only means something with --run')
    if a.bank and not (a.run or a.changed):
        raise SystemExit('--bank wants run verdicts; pair it with --run or --changed')

    compute_lock.take()
    _require_bounded()
    need_tools()
    hw = load_hardware_only()
    if hw:
        print(f'hardware-only: {len(hw)} programs classify instead of '
              f'running ({HW_ONLY_FILE.name})')
    bank = load_bank()
    if a.changed and bank is None:
        raise SystemExit('--changed needs a bank; run --run once, then --bank')
    WORK.mkdir(exist_ok=True)
    names = select_population(TESTS)
    if a.limit:
        names = names[:a.limit]
    if a.only:
        # A named set, not a prefix: the canary is chosen to COVER the changed
        # builtins, and the programs that do that are scattered through the
        # alphabet. A name that does not exist is a typo in the covering set
        # and silently running six of seven would misreport the coverage.
        want = [w.strip() for w in a.only.split(',') if w.strip()]
        have = {p.stem: p for p in names}
        missing = [w for w in want if w not in have]
        if missing:
            raise SystemExit(f'--only: no such program(s): {", ".join(missing)}')
        names = [have[w] for w in want]
    print(f'corpus: {len(names)} programs from {TESTS}')
    print(population_composition(TESTS, names))
    print(population_provenance(TESTS))

    # A limited run is a smoke test; the json files are the full-corpus census
    # and a slice must not overwrite them (one did, 2026-08-19).
    persist = not (a.limit or a.only)
    results, hist = stage_transpile(names, WORK)
    if persist:
        (WORK / 'transpile.json').write_text(json.dumps(results, indent=1))
        (WORK / 'gaps.json').write_text(json.dumps(hist.most_common(), indent=1))
    else:
        print('\n--limit run: census json left untouched')

    carried, verdicts = {}, {}

    if a.changed:
        # A verdict carries only while both halves of its cache key hold: the
        # emitted zig is byte-identical to the banked hash AND the toolchain
        # that produced the banked verdict is the toolchain that would rerun
        # it. Anything else reruns -- a stale verdict served fast is worse
        # than a fresh one served slow.
        same_zig = bank['meta']['zig'] == zig_version()
        if not same_zig:
            print(f'\nzig toolchain moved ({bank["meta"]["zig"]} -> '
                  f'{zig_version()}); no verdict carries, everything reruns')
        to_run = []
        for r in results:
            if r['stage'] != 'clean':
                continue
            if r['name'] in hw:
                to_run.append(r)      # classified, not run; never carries
                continue
            old = bank['programs'].get(r['name'])
            # The .expected content is part of the key: an Update that
            # rewrites an oracle file must rerun the program, or the bank
            # serves a match against an answer that no longer exists.
            if (same_zig and old and old.get('verdict')
                    and old.get('zig_sha') == r.get('zig_sha')
                    and old.get('expected_sha') == expected_sha(r['name'])):
                carried[r['name']] = old
            else:
                to_run.append(r)
        # Saying what was NOT run is load-bearing: an unchanged-but-broken
        # assumption must never read as green silence.
        print(f'\n--changed: {len(carried)} clean programs byte-identical to '
              f'bank {bank["meta"]["date"]}, not rerun; {len(to_run)} to run')
        tally, detail, verdicts = stage_run(to_run, WORK, persist=persist,
                                            hw=hw)
    elif a.run:
        prior = load_run_carry(results) if persist else {}
        tally, detail, verdicts = stage_run(results, WORK, persist=persist,
                                            batch=a.batch, prior=prior, hw=hw)
        if persist:
            (WORK / 'run.json').write_text(json.dumps(
                {'tally': dict(tally), 'detail': detail}, indent=1))

    if a.run or a.changed:
        print('\nfindings worth reading first:')
        for name, kind, why in detail[:25]:
            print(f'  {kind:8s} {name:32s} {why}')
        programs = assemble_census(results, carried, verdicts)
        if bank:
            print_bank_diff(bank, programs)
        if a.bank:
            unrun = [n for n, e in programs.items()
                     if e['stage'] == 'clean' and 'verdict' not in e]
            if unrun:
                raise SystemExit(f'--bank refused: {len(unrun)} clean programs '
                                 f'have no run verdict yet; finish the batches first')
            write_bank(programs)
            print(f'\nbanked {len(programs)} programs to {CENSUS}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
