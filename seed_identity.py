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


def truth_dir(slug=None):
    """Where truths for a given seed live. Banked truths are the one durable
    artifact per rung; everything else the ladder writes is regenerable and
    stays unversioned beside the rung."""
    return LADDER / 'truth' / (slug or stamp()['slug'])


def require_match(banked_sha):
    """Refuse, do not warn. A sweep that reports green against a seed it was
    not banked against is the failure this whole exercise exists to prevent."""
    actual = seed_sha256()
    if actual != banked_sha:
        raise SeedMismatch(
            f'seed on disk is {actual[:16]}, truth was banked against '
            f'{banked_sha[:16]}; re-bank or point CODEX_ROOT at the right checkout')


if __name__ == '__main__':
    s = stamp()
    named = f"Update {s['update']}" if s['update'] is not None else 'no release note names it'
    print(f"seed    {s['sha256']}")
    print(f"bytes   {s['bytes']:,}")
    print(f"update  {named}")
    print(f"truth   {truth_dir(s['slug'])}")
