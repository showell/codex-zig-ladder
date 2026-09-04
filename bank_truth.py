#!/usr/bin/env python3
"""Bank the working truths under the seed that produced them.

A truth is a measurement, not a build product. Everything else the ladder
writes regenerates from a script beside it, which is why `ast/*.truth` is in
.gitignore along with the subjects and the emitted zig -- but a truth
regenerates only by running the rung again, for an hour. So the working
copies stay unversioned beside the rung, and a bank is taken deliberately,
here.

The hour is the whole cost, and it is not the seed: `seed/Codex.cdx` is tracked
upstream, so every Update's seed is one `git show` away forever. Preciousness
here argues for keeping banks, never for rationing them.

Banking is what makes two Updates comparable. `truth/u45/u45-lower.truth` and
`truth/u46/u46-lower.truth` are the same measurement of the same rung under two
compilers, and the diff between them is the only artifact that says what an
Update actually changed in the emitted image. That is the capability the
separate repository was for, and it does not exist until something writes the
files down.

So EVERY Update is banked, including one the ladder never agreed with. A truth
is a bare-metal measurement -- `oracle_lib.sh` runs the seed under QEMU for it
and the plug's arms "live next door, because nothing they do can reach a
bare-metal truth" -- so a red zig arm cannot make one dishonest, and is not
grounds to withhold one. What the arms said is RECORDED instead, in ARMS beside
SEED. The claim they gate is the `uNN-14of14` tag, whose own name is the rule.

The Update prefix is in the name as well as the directory on purpose: a file
pulled out of its directory to be mailed, pasted or diffed still says what it
is. A bare `lower.truth` in a bug report names nothing.

A NAME COMES FROM THE SEED **AND THE TREE**, because the seed alone does not
identify a checkout. `seed/Codex.cdx` is tracked upstream and a PR against the
compiler source does not rebuild it, so a branch carrying unlanded compiler work
has the release's seed byte for byte. That is not hypothetical:
`master-plus-outbound` measured `lex.truth` at 5,335 tokens where Update 53's
release measured 5,339, first difference at PR 114's own added line, while
`parse.truth` came back byte-identical. Same seed, two trees, one of them a
release.

So a release is `u53` and anything else is `u53+<head12>` -- see
`seed_identity.measurement_slug`. **THIS REPLACED A REFUSAL, and the refusal was
the bug.** The old rule was that HEAD must BE the release commit, enforced
because the directory carried the release's name and a branch would have
overwritten it. What it cost, 2026-09-03: a complete, correct set of fourteen
`u56-candidate` truths, recorded in 1,793 seconds and then refused by the sweep
in the same script while the files sat in `ast/`. The ladder's ordinary job is
comparing a branch we understand against a branch we do not; two releases is
merely the case where both names are releases, and it was the only case this
script would record.

A bank is a SET, and taking one from a mixed working tree is the one way to
make it lie. If some rungs ran under a different seed or older harness content
than others, the directory looks like fourteen measurements of one compiler
and is not. Each truth carries a provenance sidecar (truth_prov.py, written by
the truth arm: the seed sha and the harness-content sha it was measured
under), and this refuses to bank any truth whose sidecar is missing or
disagrees with what is on disk now -- content identity, not timestamps. The
bank itself is written to a temp directory and renamed into place, so a crash
or a --force can never leave a directory that is half one measurement and
half another.
"""

import argparse
import shutil
import sys

import truth_prov
from ladder_root import LADDER
from seed_identity import measurement_slug, stamp, tree_stamp, truth_dir

# What a bank must contain. Taken from oracle_lib.sh so the two cannot drift
# about what the ladder is: a rung missing from the bank is a rung whose truth
# quietly is not there when someone reaches for it.
def ladder_rungs():
    text = (LADDER / 'ast' / 'oracle_lib.sh').read_text()
    for line in text.splitlines():
        if line.startswith('LADDER_RUNGS='):
            return line.split('"')[1].split()
    raise SystemExit('oracle_lib.sh: no LADDER_RUNGS= line; cannot tell what the ladder is')


def arm_verdict(rungs):
    """What the zig arms said about these truths, derived rather than declared.

    An arm writes `ast/<rung>.diff`: empty when the emitted zig matched the
    bare-metal truth byte for byte, the differences when it did not. ABSENT is
    a third state and it is not a synonym for red -- `zig_arm` returns before
    it diffs anything when the zig will not build, so a unit that failed to
    compile leaves every rung it carries with no diff at all. That is what "6
    of 14" meant for Update 52: six agreed, and eight never got a verdict.

    Nothing here gates the bank. A reader diffing two banks needs to know which
    of them the ladder actually agreed with, and the bank is the only artifact
    that travels with the answer.
    """
    ast = LADDER / 'ast'
    agreed, differed, no_result, stale = [], [], [], []
    for m in rungs:
        d = ast / f'{m}.diff'
        if not d.is_file():
            no_result.append(m)
            continue
        # A FOURTH state, and it used to be invisible. The three above are read
        # off a file's existence and size, which says what a verdict WAS but
        # not that this tree produced it. `check_diff` compares the recorded
        # (seed, truth, emitted zig) against what is on disk now; a verdict
        # carried in from another sandbox, or taken before a re-pin, lands here
        # instead of being counted as an agreement.
        why = truth_prov.check_diff(m, truth_prov.unit_of(m))
        if why:
            stale.append((m, why))
        elif d.stat().st_size == 0:
            agreed.append(m)
        else:
            differed.append(m)
    return agreed, differed, no_result, stale


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--force', action='store_true',
                    help='bank an incomplete set, or a tree that is not the release '
                         'the seed names; each refusal confirms separately')
    args = ap.parse_args()

    s = stamp()
    slug = measurement_slug()
    dest = truth_dir(slug)
    ast = LADDER / 'ast'

    named = f"Update {s['update']}" if s['update'] is not None else 'no release note names it'
    print(f"seed   {s['sha256'][:16]}  ({s['bytes']:,} bytes)")
    print(f"update {named}")
    print(f"bank   {dest}")

    # WHICH TREE. The seed says which release; it cannot say which checkout,
    # and the two come apart exactly when it matters -- on a branch carrying
    # compiler work that has not landed. Only a bank NAMED for a release can
    # overwrite one, so an unreleased seed (slug `seed-<hash>`) needs no gate
    # here: its name collides with nothing.
    t = tree_stamp()
    # A release can ship as more than one commit -- Update 54 shipped the seed
    # in c689cafb and corrected its release note in 14ec571b -- so the gate is
    # `measures_release`, which allows a tail the ladder provably cannot read
    # (docs/ only) and nothing else. `is_release` stays the narrow fact and is
    # still what TREE reports.
    at_release = t['measures_release'] and t['release_seed'] == s['sha256']
    print(f"tree   {t['head'][:12]}  {t['branch']}")
    if t['is_release']:
        print(f"       release {t['release'][:12]}  -- HEAD is it")
    else:
        print(f"       release {t['release'][:12]}  -- HEAD is "
              f"{len(t['tail'])} commit(s) past it"
              + ('  (docs only -- the ladder reads none of it)'
                 if at_release else '  -- HEAD IS NOT IT'))
        for line in t['tail']:
            print(f"         + {line}")
        for path in t['tail_paths']:
            print(f"           {path}")
    off_release = None
    # NO GATE HERE ANY MORE, and its absence is the point. This used to REFUSE
    # to save unless HEAD was the release commit, because the directory was
    # named for the release and a branch's truths would have overwritten it.
    # The name now carries the tree, so a branch's measurements cannot collide
    # with a release's and there is nothing left to protect.
    #
    # What that gate actually cost, measured 2026-09-03: a complete, correct set
    # of fourteen `u56-candidate` truths, recorded in 1,793 seconds and then
    # refused by the sweep in the same script -- "no bank for this seed" --
    # while the files sat in ast/. The ladder's ordinary job is comparing a
    # branch we understand to a branch we do not; Update N against Update N+1 is
    # just the case where both happen to be releases, and it was the only case
    # this script would let you record.
    print()

    # A truth is bankable when its recorded provenance -- the seed it ran
    # under and the harness content its subject was built from, stamped by
    # the truth arm -- matches what is on disk NOW. split_truth.py is in the
    # watched set because a truth file is the splitter's output, not the
    # run's: a splitter that cut the stream somewhere else would produce
    # truths wrong in a way no diff of the run can see.
    rungs = ladder_rungs()
    missing, stale, ready = [], [], []
    for m in rungs:
        src = ast / f'{m}.truth'
        if not src.is_file() or src.stat().st_size == 0:
            missing.append(m)
            continue
        prov = truth_prov.read_sidecar(m)
        if prov is None:
            stale.append((m, 'no provenance sidecar (rerun the truth arm)'))
            continue
        pseed, pset = prov
        if pseed != s['sha256']:
            stale.append((m, f'ran under seed {pseed[:12]}, disk has '
                             f'{s["sha256"][:12]}'))
        elif pset != truth_prov.set_hash(truth_prov.unit_of(m)):
            stale.append((m, 'harness content moved since it ran'))
        else:
            ready.append((m, src))

    if missing:
        print(f'NOT BANKED: {len(missing)} rung(s) have no truth: {" ".join(missing)}')
    for m, why in stale:
        print(f'NOT BANKED: {m}: {why}')
    if (missing or stale) and not args.force:
        print('\nA partial bank reads as a whole one. Run rebank_all.sh, or pass '
              '--force if you mean to bank an incomplete set.')
        return 1

    # --force is destructive, not convenient: the rename REPLACES the whole
    # bank with the ready subset. Confirm by the count, so agreeing requires
    # having read it (C3). Non-interactive stdin refuses rather than assumes.
    if (missing or stale) and args.force:
        print(f'\n--force: about to REPLACE {dest.name} with {len(ready)} of '
              f'{len(rungs)} rungs; the {len(rungs) - len(ready)} others '
              'vanish from the bank.')
        try:
            answer = input(f'type the ready count ({len(ready)}) to confirm: ')
        except EOFError:
            answer = ''
        if answer.strip() != str(len(ready)):
            print('confirmation mismatch; nothing banked')
            return 1

    # Since the rename REPLACES the destination, an empty ready set must stop
    # here even under --force: a SEED-only directory renamed over a full bank
    # would destroy fourteen measurements to record zero.
    if not ready:
        print('NOTHING TO BANK: no rung is ready; refusing to replace '
              f'{dest.name} with an empty set')
        return 1

    # Built complete in a temp directory, then renamed over the old bank, so
    # the destination is only ever a whole set -- never last bank's files
    # beside this one's after a crash or a --force of a subset.
    tmp = dest.parent / (dest.name + '.tmp')
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    banked_prov = 0
    for m, src in ready:
        shutil.copy2(src, tmp / f"{slug}-{m}.truth")
        # The sidecar travels WITH the truth. A banked truth without its
        # provenance is a measurement nobody can place afterwards: SEED
        # below records the seed, but a truth is keyed on the seed AND the
        # harness content it was measured under, and only the sidecar
        # carries the second. Restoring a bank into a fresh sandbox is
        # then a copy rather than a re-measurement, and it stays HONEST
        # because truth_prov.check still validates the restored sidecar
        # against what is on disk now -- a harness that moved since the
        # bank was taken refuses exactly as it always did. Nothing is
        # loosened here; something previously thrown away is kept.
        prov = truth_prov.sidecar(m)
        if prov.is_file():
            shutil.copy2(prov, tmp / f"{slug}-{m}.truth.prov")
            banked_prov += 1
    (tmp / 'SEED').write_text(f"{s['sha256']}\n{s['bytes']}\n{s['update']}\n")
    # TREE is the answer SEED could never give. A reader holding two banks and
    # asking what changed between them needs to know they describe two
    # releases and not two branches; before this file, nothing in a bank said.
    # The TAIL is written down whenever there is one. A gate that ACCEPTS
    # something has to leave the reader able to see what it accepted, or it
    # has bought silence rather than honesty: a bank whose TREE says only
    # "HEAD is the release" would hide the two commits Update 54 shipped on
    # top of its seed commit, and the next reader could not tell this tree
    # from one carrying unlanded compiler work.
    tail = ''
    if t['tail']:
        tail = ('tail     ' + f"{len(t['tail'])} commit(s) after the release commit"
                + (', touching docs/ only -- the ladder reads none of it\n'
                   if t['measures_release'] else ', NOT inert\n')
                + ''.join(f'         + {l}\n' for l in t['tail'])
                + ''.join(f'           {p}\n' for p in t['tail_paths']))
    (tmp / 'TREE').write_text(
        f"head     {t['head']}\n"
        f"branch   {t['branch']}\n"
        f"release  {t['release']}\n"
        + tail
        + ('verdict  HEAD is the release commit this seed belongs to\n'
           if t['is_release'] else
           'verdict  HEAD is the release commit plus a docs-only tail; the '
           'ladder measures the release exactly\n'
           if at_release else
           f'verdict  NOT THE RELEASE, banked with --force: {off_release}\n'))
    agreed, differed, no_result, stale_arms = arm_verdict(rungs)
    arms = [f'agreed {len(agreed)} of {len(rungs)}']
    if differed:
        arms.append(f'differed {len(differed)}: {" ".join(differed)}')
    if no_result:
        arms.append(f'no result {len(no_result)}: {" ".join(no_result)}')
    # An unprovenanced verdict is reported as its own state, never folded into
    # one of the other three. Silently counting it as an agreement is the whole
    # defect this state exists to name.
    if stale_arms:
        arms.append(f'unprovenanced {len(stale_arms)}: '
                    + '; '.join(f'{m} ({why})' for m, why in stale_arms))
    (tmp / 'ARMS').write_text('\n'.join(arms) + '\n')
    if dest.exists():
        shutil.rmtree(dest)
    tmp.rename(dest)
    print(f"banked {len(ready)} truths as {slug}-<rung>.truth")
    # The arms are reported, never enforced. A bank taken before the zig arms
    # have run at all is a complete bank of bare-metal truths whose ARMS says
    # so, which is the ordinary state now that bare metal goes first.
    for line in arms:
        print(f'       arms: {line}')
    # Say it either way. A bank whose sidecars are missing still works as a
    # bank and CANNOT be restored from, and a reader who is told only the
    # truth count has no way to know which kind they have.
    if banked_prov == len(ready):
        print(f"       {banked_prov} provenance sidecars beside them "
              "(this bank can be restored into a fresh sandbox)")
    else:
        print(f"       {banked_prov} of {len(ready)} provenance sidecars -- "
              "this bank CANNOT be restored from; re-bank from a tree that "
              "has them if you want that")

    # Every bank is kept. There was a --keep 3 here that pruned by Update
    # number, and it had already deleted u45 through u48 from the working tree;
    # banking u53 would have taken u49. It rationed nothing worth rationing --
    # a bank is 1.2 MB of text against a 31 MB .git -- and removing one from
    # the working tree does not shrink git, which holds every byte regardless.
    # Its stated reason was legibility, "small enough to scan", but nobody
    # scans 332 KB of x86 output; bank_diff.sh is what makes a bank legible and
    # it reads the pair it is given.
    return 0


if __name__ == '__main__':
    sys.exit(main())
