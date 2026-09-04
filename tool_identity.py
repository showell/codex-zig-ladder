"""What a native tool was built FROM, in terms that survive relocation.

A native's own sha cannot answer this. Zig bakes the build directory into
every binary it produces -- for stack traces, reasonably -- so `native/zigemit`
built in one sandbox and the same source built in another differ in bytes
while being the same tool. Ladder runs happen in a fresh sandbox by design, so
a binary sha moves on every run whatever the source did.

That broke two mechanisms in opposite directions before this module existed
(2026-08-29). `natives_stamp()` comparisons across runs could only ever report
a difference, so a guard written as "the stamp must have changed, or the fix
never reached the build" could only ever pass. `corpus_run.bank_describes_this_tree`
compared the same shas and so could only ever say the bank was stale, which
made the census banner fire on every run and a re-bank pointless.

The fix is to name a tool by its INPUTS. `build_one` in src/native_lib.sh
bundles a subject, compiles it to IR with the seed, pushes that IR through the
ring plug, and builds the emitted zig. Four things decide the binary and
nothing else does:

    the bundled subject   what this tool IS
    the ring plug bundle  what transpiled it
    the seed              what compiled it
    the zig version       what linked it

None of them mentions a path, which is the property that makes the answer
portable: the same four inputs in any directory give the same fingerprint.

This list was already written once, inline in zigc_verify.sh, where it caches
a seven-minute build behind an 8.7-second check. corpus_run.py is the second
user, which is when the noun gets a name.
"""

import hashlib
import pathlib
import subprocess

import seed_identity

HERE = pathlib.Path(__file__).resolve().parent
AST = HERE / 'src'

# The bundle each tool is built from. The names differ because the bundlers
# do -- zigemit's is `-source`, the other two are `-subject` -- and that is
# upstream of nothing, so it is recorded rather than normalised.
SUBJECT = {
    'codexir': 'codexir-subject.codex',
    'zigemit': 'zigemit-source.codex',
    'zigc': 'zigc-subject.codex',
}

PLUG = 'ringplug-source.codex'


def zig_version():
    return subprocess.run(['zig', 'version'], capture_output=True,
                          text=True).stdout.strip()


def built_from(name):
    """The fingerprint of `name`'s four inputs, or None if any is absent.

    None is not a failure to report as a difference. It means the tree has
    not been bundled yet -- a fresh sandbox before its first build -- and a
    caller comparing fingerprints must treat "I cannot tell" as its own
    answer rather than as "not equal", which is the mistake this module was
    written to stop making.
    """
    subject = AST / SUBJECT[name]
    plug = AST / PLUG
    # BOTH, and both are gitignored, so a fresh worktree genuinely has
    # neither and this returns None rather than fingerprinting something no
    # build here produced. That was a coincidence until 2026-08-29:
    # zigemit-source.codex was tracked, so a fresh tree carried a stale copy,
    # and only the ring plug bundle's absence kept the answer honest. It is
    # untracked now and the guarantee is real -- see README, "One sandbox per
    # experiment". Keep it that way: a tracked input here means a fresh tree
    # starts answering confidently and wrongly.
    if not (subject.is_file() and plug.is_file()):
        return None
    h = hashlib.sha256()
    h.update(subject.read_bytes())
    h.update(plug.read_bytes())
    h.update(seed_identity.seed_sha256().encode())
    h.update(zig_version().encode())
    return h.hexdigest()[:16]


def natives():
    """Both tools corpus_run measures with, as name -> fingerprint."""
    return {n: built_from(n) for n in ('codexir', 'zigemit')}


if __name__ == '__main__':
    for n in ('codexir', 'zigemit', 'zigc'):
        print(f'{n:9s} {built_from(n) or "(not bundled in this tree)"}')
