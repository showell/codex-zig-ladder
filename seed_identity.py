#!/usr/bin/env python3
"""What the ladder is running against, derived rather than declared.

A banked truth is only meaningful together with the seed that produced it. The
Update number is a label people say out loud; the seed's SHA-256 is the thing
that actually decides whether a banked byte is still the right byte. So the
label is derived FROM the seed here, never typed alongside it.

The obvious derivation -- take the highest-numbered GitHubUpdate file -- is
wrong, and wrong today. Update 45's release commit creates GitHubUpdate46.md as
the accumulator for the next Update, so the highest file names an Update that has
not shipped and whose seed does not exist. Instead: the release note that names
our seed's hash IS our Update. That cannot drift, because a note only names a
hash once the release built it.

A seed no note names is not an error, but it is not Update N either -- it is an
unreleased or locally rebuilt seed, and it says so. Banking truth against one is
fine; pretending it was a release is not.
"""

import hashlib
import pathlib
import re
import subprocess

from ladder_root import CODEX, LADDER

SEED = CODEX / 'seed' / 'Codex.cdx'
NOTES = CODEX / 'docs' / 'PM' / 'Active' / 'GitHubUpdates'

# Release notes name the seed by its leading eight hex digits, uppercased
# ("seed 270227BE at 2,827,487 bytes"). Damian's top-level README carries the
# full digest; either spelling identifies it, so match on the prefix both share.
PREFIX_LEN = 8


class SeedMismatch(RuntimeError):
    """The seed on disk is not the seed a truth was banked against."""


def seed_sha256():
    return hashlib.sha256(SEED.read_bytes()).hexdigest()


def update_label(sha):
    """The Update whose release note names this seed AS ITS RELEASE, or None.

    Naming is restricted to the three release forms the notes actually use --
    a table row marked "release seed" beside the hash, the closing prose
    header that begins "Seed `<hash>`", or the "Release measurements"
    section header that names the seed inline (the Update 48 form; interim
    sections are titled "Interim mirror push" and never match), or the
    artifacts table's `seed/Codex.cdx` row under "measured at the release
    head" (the Update 49 form), or a BOLDED line that names both the release
    head and the seed -- because a
    bare substring match
    labels too much: prior-release seeds are back-referenced in later notes
    ("The release 46 seed was ..."), and interim seeds are named in the next
    Update's accumulator, so an interim checkout would get a release number
    it never earned. Two notes claiming one seed is a refusal, not a sort.

    That last arm is bold-anchored rather than prose-anchored because the
    back-reference is the near miss, not a distant one. Update 52 names its
    release seed as "**The proofs, all at the release head against seed
    `<hash>`:**" and Update 53's accumulator opens "through its release head
    (main 20354, seed `<hash>`)" -- same two phrases, same seed, one line
    apart in shape. Only the release announcement is bolded, so requiring the
    bold is what keeps 52 and 53 from both claiming it and turning a correct
    label into the two-notes refusal. It also covers the Update 50 form
    ("**Release head: main <N>. Seed `<hash>`"), which it replaced rather
    than joined. The hash is matched without its closing backtick because
    Update 51 spells it in eight digits and Update 52 in sixteen.

    THE RIGHT FIX IS TO STOP READING THE NOTES. Damian told us on issue 97,
    2026-08-28, that the digest was published at our pin all along -- it moved
    to `TechnicalDetails.md`, which is in the release commit -- and that the
    release notes are not getting it back. That file carries the full 64 hex
    digits and did so at Update 53's pin too. Four Updates have named the seed
    four different ways in the notes and this function has needed teaching
    twice; the digest file has been stable throughout. Moving to it is ours to
    do and is not done yet.

    The word `seed` before the hash is NOT required, and dropping it is what
    Update 53 cost. Its line is "**The proofs, all at the release head
    against `<hash>`:**" -- Update 52's line to the character except that the
    word is gone -- so an arm keyed on "SEED `<hash>`" missed it, and the
    release would have banked as `seed-b066ceb5` rather than `u53`. Caught by
    the canary before the rebank, which is the second time this function has
    needed teaching by a new release form (Update 50 was the first). The
    relaxation is safe by census rather than by argument: across every note in
    the tree there are FOUR bolded lines containing "release head" and three
    carry a hash, each its own Update's. The bold is still doing the work that
    separates a release announcement from the back-reference one line away.
    """
    prefix = sha[:PREFIX_LEN].upper()
    claims = []
    for note in sorted(NOTES.glob('GitHubUpdate*.md')):
        m = re.search(r'GitHubUpdate(\d+)\.md$', note.name)
        if not m:
            continue
        for line in note.read_text(errors='replace').upper().splitlines():
            if prefix in line and ('RELEASE SEED' in line
                                   or 'RELEASE MEASUREMENTS' in line
                                   or line.strip().lstrip('*').startswith('SEED `')
                                   or line.strip().startswith('| `SEED/CODEX.CDX` |')
                                   or (line.strip().startswith('**')
                                       and 'RELEASE HEAD' in line
                                       and f'`{prefix}' in line)):
                claims.append(int(m.group(1)))
                break
    if len(claims) > 1:
        raise SystemExit(f'seed {prefix} claimed as the release seed by '
                         f'Updates {claims}; the notes must disagree less')
    return claims[0] if claims else None


def stamp():
    sha = seed_sha256()
    label = update_label(sha)
    return {
        'sha256': sha,
        'bytes': SEED.stat().st_size,
        'update': label,
        # What a truth directory is named. An unreleased seed gets its hash
        # rather than a number, so it can never be mistaken for a release.
        'slug': f'u{label}' if label is not None else f'seed-{sha[:PREFIX_LEN]}',
    }


def _git(*args):
    """git in the codex checkout, and a failure here is fatal by design.

    Everything below answers "which tree", and a "(unknown)" for that is worse
    than no answer: it is the silent shrug that let a bank claim a seed and say
    nothing about the branch. A checkout that cannot answer refuses instead.
    """
    r = subprocess.run(['git', '-C', str(CODEX), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f'{CODEX}: git {" ".join(args)} failed -- a bank cannot '
                         f'say which tree it describes\n{r.stderr.strip()}')
    return r.stdout.strip()


def codex_branch(rev='HEAD'):
    """Which branch this rev is, or which branches contain it.

    A sandbox checkout is a DETACHED worktree, so `--abbrev-ref HEAD` answers
    the literal word `HEAD` -- true, and no help to the next reader. The commit
    is the authority; this is for placing it by eye, so a detached head names
    the branches that contain it rather than a word describing every detached
    tree ever made.
    """
    ref = _git('rev-parse', '--abbrev-ref', rev)
    if ref != 'HEAD':
        return ref
    names = [l.strip() for l in
             _git('branch', '--all', '--contains', rev,
                  '--format=%(refname:short)').splitlines()
             if l.strip() and not l.strip().startswith('(')]
    return f'(detached) contained by: {", ".join(names)}' if names else \
        '(detached, no branch contains it)'


def tail_is_inert(paths):
    """Can the ladder read ANY of these paths? If not, a tail touching only
    them cannot move a truth or an arm.

    Pure, and separated from git for one reason: this is the whole judgment in
    `measures_release`, and a judgment reachable only by constructing a branch
    is a judgment nobody re-checks. `--gate` below exercises it directly.

    `docs/` is the only inert prefix and the list is deliberately not longer.
    The ladder reads `seed/`, `codex/`, `build/` and `tools/`; a root-level
    file (`.p4ignore`, a README) is not obviously any of those, and guessing
    in the permissive direction is how a gate stops being one. An empty list
    is NOT inert -- no tail at all is `is_release`, which is a different and
    stronger fact, and answering True here would blur the two.
    """
    return bool(paths) and all(p.startswith('docs/') for p in paths)


def tree_stamp(rev='HEAD'):
    """WHICH TREE -- the half of a bank's identity the seed cannot supply.

    A seed identifies a RELEASE. It does not identify a CHECKOUT.
    `seed/Codex.cdx` is tracked upstream and a PR against the compiler source
    does not rebuild it, so a branch carrying unlanded compiler work has the
    release's seed byte for byte. `stamp()` alone therefore labels our own
    stack `u53`, and a bank taken there overwrites the release bank under the
    release's name with nothing refusing it. Measured 2026-09-01 on
    `master-plus-outbound`: same seed, `lex.truth` 5,339 -> 5,335 tokens.

    The release commit needs no table to look it up in. The seed changes only
    when a release rebuilds it, so THE NEWEST COMMIT REACHABLE FROM HEAD THAT
    TOUCHED `seed/Codex.cdx` IS the release this checkout descends from, and
    everything after it is work that release does not contain. Deriving it
    keeps this honest across Updates nobody has taught it about, which is the
    failure `update_label` has now had twice.

    `is_release` is the narrow verdict: the rev IS that commit, or it is not.
    `rev` is a parameter so the refusal can be exercised against a branch that
    should trip it WITHOUT checking that branch out -- a gate nobody has seen
    fire is a gate nobody knows works.

    A RELEASE CAN SHIP AS MORE THAN ONE COMMIT, and Update 54 did: `c689cafb`
    carried the seed and `14ec571b` corrected the release note two hours later
    (PR 100 is not on main, nine of ten are). The pin sits on the correction,
    so `is_release` is False on a tree that is the release in every respect the
    ladder can measure. `--force` is the wrong answer to that -- it writes
    "NOT THE RELEASE" into the bank's TREE file, which is a false statement.

    So the tail is DERIVED and CLASSIFIED rather than asserted. `tail` is every
    commit after the release commit; `tail_paths` is what they touch;
    `measures_release` is True when the tail is empty (`is_release`) or touches
    NOTHING OUTSIDE `docs/`. The ladder never reads `docs/` -- not the seed, not
    `codex/`, not `build/`, not `tools/` -- so a docs-only tail cannot move a
    truth or an arm, and that is a mechanical fact rather than a judgment about
    what a commit meant. Anything else, including a root-level file, is not
    inert and still needs `--force`.

    The tail is CARRIED, not swallowed. A caller that accepts it has to say so
    in the artifact it writes, or this has bought silence instead of honesty.
    """
    head = _git('rev-parse', rev)
    release = _git('log', '-1', '--format=%H', rev, '--', 'seed/Codex.cdx')
    if not release:
        raise SystemExit(f'no commit reachable from {rev} touches seed/Codex.cdx; '
                         'this checkout cannot say which release it descends from')
    blob = subprocess.run(['git', '-C', str(CODEX), 'show',
                           f'{release}:seed/Codex.cdx'], capture_output=True)
    tail = [l for l in _git('log', '--format=%h %s', f'{release}..{head}').splitlines() if l]
    tail_paths = sorted({l for l in _git('diff', '--name-only',
                                         f'{release}..{head}').splitlines() if l})
    inert = tail_is_inert(tail_paths)
    return {
        'head': head,
        'branch': codex_branch(rev),
        'release': release,
        # The seed that commit CARRIES, against the seed on disk. They differ
        # when the working seed was rebuilt locally, and then the bank's name
        # comes from a seed no commit in this history ever introduced.
        'release_seed': hashlib.sha256(blob.stdout).hexdigest(),
        'is_release': head == release,
        'tail': tail,
        'tail_paths': tail_paths,
        # A tree the ladder cannot tell apart from the release commit.
        'measures_release': head == release or inert,
    }


def measurement_slug(rev='HEAD'):
    """What a set of truths is OF: the seed, and the tree if it is not a release.

    **THE OLD NAMING WAS THE WHOLE PROBLEM.** A directory named for the release
    the seed came from is the right name for exactly one tree -- the release --
    and the wrong name for every branch that shares that seed, because
    `seed/Codex.cdx` is tracked upstream and our own compiler work does not
    rebuild it. So a branch's measurements wanted to land on top of the
    release's, under the release's name, and the only thing standing between
    them was a gate that REFUSED TO SAVE AT ALL. Measured 2026-09-03: a
    complete, correct set of fourteen `u56-candidate` truths was recorded in
    1,793 seconds and then refused by the sweep in the same script, because it
    had nowhere to live that was not a lie.

    A branch gets its own name instead. Nothing collides, so nothing needs
    guarding, and comparing branch A to branch B is the ordinary case rather
    than the exception -- which is what the ladder actually does. Comparing
    Update N to Update N+1 is just the case where both names happen to be
    releases.
    """
    s = stamp()
    t = tree_stamp(rev)
    if t['measures_release'] and t['release_seed'] == s['sha256']:
        return s['slug']
    return f"{s['slug']}+{t['head'][:12]}"


def truth_dir(slug=None):
    """Where truths for a given measurement live. Banked truths are the one
    durable artifact per rung; everything else the ladder writes is regenerable
    and stays unversioned beside the rung.

    Defaults to `measurement_slug()`, which is the seed's slug for a release and
    `<slug>+<head12>` for anything else."""
    return LADDER / 'truth' / (slug or measurement_slug())


def require_match(banked_sha):
    """Refuse, do not warn. A sweep that reports green against a seed it was
    not banked against is the failure this whole exercise exists to prevent."""
    actual = seed_sha256()
    if actual != banked_sha:
        raise SeedMismatch(
            f'seed on disk is {actual[:16]}, truth was banked against '
            f'{banked_sha[:16]}; re-bank or point CODEX_ROOT at the right checkout')


def _gate_selftest():
    """Show the release gate firing, in both directions, with no branch names.

    BOX Before-11: a comparison whose every row reads ok has never executed its
    own mismatch branch. Each row here is a tail the ladder either can or
    cannot read, and the REFUSING rows are the ones that give this its value.
    """
    cases = [
        ([], False, 'no tail at all -- that is is_release, not this'),
        (['docs/PM/CurrentPlan.md'], True, 'a release-note correction'),
        (['docs/a.md', 'docs/b.md'], True, 'two docs files'),
        (['docs/a.md', 'codex/compiler/Syntax/Lexer.codex'], False,
         'MIXED -- one readable path is enough to refuse'),
        (['codex/plugs/zig/ZigEmitter.codex'], False, 'the emitter under test'),
        (['seed/Codex.cdx'], False, 'the seed itself'),
        (['build/compile.ps1'], False, 'the harness the arms drive'),
        (['.p4ignore'], False, 'a root file: not obviously unread, so refused'),
    ]
    bad = 0
    for paths, want, why in cases:
        got = tail_is_inert(paths)
        if got != want:
            bad += 1
        print(f"{'ok ' if got == want else 'RED'} inert={str(got):5} "
              f"want={str(want):5} {why}\n      {paths}")
    print('\nthe gate fires in both directions' if not bad
          else f'\n{bad} ROW(S) RED -- the gate does not do what it says')
    return 1 if bad else 0


if __name__ == '__main__':
    import sys as _sys
    if '--gate' in _sys.argv:
        raise SystemExit(_gate_selftest())
    s = stamp()
    named = f"Update {s['update']}" if s['update'] is not None else 'no release note names it'
    print(f"seed    {s['sha256']}")
    print(f"bytes   {s['bytes']:,}")
    print(f"update  {named}")
    print(f"truth   {truth_dir(s['slug'])}")
    t = tree_stamp()
    print(f"head    {t['head'][:12]}  {t['branch']}")
    print(f"release {t['release'][:12]}  "
          + ('HEAD IS the release commit' if t['is_release']
             else f"HEAD is {len(t['tail'])} commit(s) past it, docs only "
                  '-- the ladder measures the release exactly'
             if t['measures_release']
             else 'HEAD carries work the release does not'))
    for line in t['tail']:
        print(f"        + {line}")
    for path in t['tail_paths']:
        print(f"          {path}")
