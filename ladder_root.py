#!/usr/bin/env python3
"""The two roots the ladder needs, resolved in one place.

Every script here used to derive its roots by walking a fixed number of
directories up from itself, which worked only because the ladder sat inside the
Codex checkout: the ladder root was `..` and the checkout was `../..`. Ninety-odd
sites did that, and they already disagreed -- src/gen_scale_harness.py walked two
levels and src/gen_check_harness.py walked three, meaning one of them wanted the
ladder and the other wanted the checkout, and nothing said which.

Once the ladder lives in its own repository the two are unrelated paths, so the
level count cannot encode the answer any more. Both roots are named here instead,
and a caller says which one it means.

LADDER is where this file is: the ladder's own tree, always known.

CODEX is the checkout under test. It comes from $CODEX_ROOT when that is set --
which is how one ladder gets pointed at several Updates in turn -- and otherwise
from the first directory at or above LADDER that looks like a checkout. Nothing
is guessed: a directory qualifies only by holding the compiler's driver, and a
failed search raises rather than falling back to a plausible-looking path. A
ladder silently pointed at the wrong checkout would bank truth against a seed
nobody named, which is the one failure this whole exercise exists to prevent.
"""

import os
import pathlib

# The compiler's driver. A directory holding this is a Codex checkout; a
# directory not holding it is not, whatever it is called.
MARKER = pathlib.Path('codex') / 'compiler' / 'opening.codex'

LADDER = pathlib.Path(__file__).resolve().parent


class CodexRootError(RuntimeError):
    """No checkout found, or the one named is not a checkout."""


def _is_checkout(path):
    return (path / MARKER).is_file()


def codex_root():
    """The Codex checkout to run against. Raises rather than guessing."""
    named = os.environ.get('CODEX_ROOT')
    if named:
        path = pathlib.Path(named).expanduser().resolve()
        if not _is_checkout(path):
            raise CodexRootError(
                f'CODEX_ROOT={named} is not a Codex checkout: no {MARKER} under {path}')
        return path

    for candidate in (LADDER, *LADDER.parents):
        if _is_checkout(candidate):
            return candidate

    raise CodexRootError(
        f'no Codex checkout at or above {LADDER} (looked for {MARKER}); '
        f'set CODEX_ROOT to the checkout you mean')


class OutRootError(RuntimeError):
    """No sandbox to write into, and a checkout is not an acceptable substitute."""


def out_root():
    """Where everything GENERATED goes. The sandbox, never a git checkout.

    **THIS IS THE THIRD ROOT AND IT SHOULD HAVE BEEN THERE FROM THE START.**
    LADDER and CODEX are both places to READ. Nothing named a place to WRITE, so
    every generator wrote beside itself and every cycle wrote beside the rung it
    ran -- which put 343 MB of harnesses, subjects, blobs, emitted zig and truths
    inside a 4 MB source repository, invisible because .gitignore covered for it.

    `$SANDBOX/work` when a sandbox is set, and `sandbox.sh` sets it. **A missing
    sandbox is a REFUSAL, not a fallback to the checkout** -- falling back is
    precisely how the checkout filled up, and a fallback that is convenient
    every time is a rule that is enforced none of the time.

    `LADDER_OUT` overrides, for a one-off that genuinely has nowhere else to go.
    It has to be named, which is the point: an override in a command line is a
    decision somebody made and can be read back, where a silent default is not.
    """
    named = os.environ.get('LADDER_OUT')
    if named:
        path = pathlib.Path(named).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    sandbox = os.environ.get('SANDBOX')
    if not sandbox:
        raise OutRootError(
            'no $SANDBOX, so there is nowhere to write generated files.\n'
            '  Generated output belongs in a sandbox -- one sandbox, one commit -- '
            'and never in a checkout.\n'
            '  Cut one:  ./sandbox.sh <label> [ladder-ref] [codex-repo] [codex-ref]\n'
            '  Or name a directory explicitly:  LADDER_OUT=<dir>')
    path = pathlib.Path(sandbox).expanduser().resolve() / 'work'
    path.mkdir(parents=True, exist_ok=True)
    return path


CODEX = codex_root()


if __name__ == '__main__':
    # The shell and PowerShell drivers ask through this, so the policy -- the
    # variable name, the marker, the error text -- has exactly one home.
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else 'codex'
    print(CODEX if which == 'codex' else out_root() if which == 'out' else LADDER)
