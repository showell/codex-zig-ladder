#!/usr/bin/env python3
"""The foreword's numeric routines, what each claims, and how to grade it.

    ./catalog.py            grade everything that needs no guest
    ./catalog.py cordic     just one

THE DOCSTRINGS ARE A SPECIFICATION NOBODY CHECKS. That is the whole reason this
exists: `Math chapter Cordic` claimed ~0.1% accuracy for however long, and
nothing in the depot or here compared that number to the routine's behaviour.
Every entry below carries the claim as written, so the claim is graded too.

A routine goes in here when it can be modelled faithfully in Python -- integer
fixed-point transcribes exactly, and that costs no box time. A routine that
cannot (anything whose answer depends on the emitted code) belongs in a
bare-metal rig like findings/atan/ instead, and is listed here as absent rather
than silently skipped.
"""
import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # ladder-root-bootstrap
from ladder_root import LADDER
sys.path.insert(0, str(LADDER / 'findings' / 'numeric'))
sys.path.insert(0, str(LADDER / 'findings' / 'cordic'))
from oracle import grade, Claim

ENTRIES = {}

CORDIC_VALIDATION = ("reproduces all 18 cordic values in the depot's committed "
                     "math-cordic-quadrants.expected, and bare metal agreed on "
                     "all 20 angles of math-cordic-accuracy (2026-08-30)")


def entry(fn):
    ENTRIES[fn.__name__] = fn
    return fn


@entry
def cordic():
    """cordic-sin and cordic-cos, over the whole turn.

    The model is `findings/cordic/model.py`, validated twice before it was
    trusted with a docstring correction: it reproduces all 18 cordic values in
    the depot's own math-cordic-quadrants.expected, and bare metal agreed with
    it on all 20 angles the new test uses.
    """
    from model import sincos, SCALE
    angles = list(range(0, 6284))
    claim = Claim(figure=0.001, reading='UNSTATED', scale=SCALE,
                  source='Math chapter Cordic docstring, "~0.1% accuracy"')
    sin_r = grade('cordic-sin', angles,
                  subject=lambda a: sincos(a)[1],
                  reference=lambda a: math.sin(a / SCALE) * SCALE,
                  claim=claim, rel_floor=SCALE * 0.1,
                  validated=CORDIC_VALIDATION)
    cos_r = grade('cordic-cos', angles,
                  subject=lambda a: sincos(a)[0],
                  reference=lambda a: math.cos(a / SCALE) * SCALE,
                  claim=claim, rel_floor=SCALE * 0.1,
                  validated=CORDIC_VALIDATION)
    return [sin_r, cos_r]


# GEODESIC IS DELIBERATELY ABSENT, and saying so is the point.
#
# `geo-sin`, `geo-cos` and `geo-atan` in Math chapter Geodesic are milliradian
# integer approximations and would model exactly like Cordic. The first draft of
# this file transcribed geo-sin by hand and reported a worst error of 7.5% at
# the quadrant edge -- a number produced by a transcription nobody had checked
# against anything, which is indistinguishable in print from a measurement.
#
# It comes back when its model is validated the way Cordic's was: against values
# the depot itself records, or against bare metal. Until then an absent entry is
# more honest than a plausible one, and Geodesic claims no accuracy anywhere, so
# nothing is going stale in the meantime.


def main():
    want = sys.argv[1:] or sorted(ENTRIES)
    bad = 0
    for name in want:
        if name not in ENTRIES:
            print(f'no such entry: {name}; have {", ".join(sorted(ENTRIES))}')
            return 2
        for rep in ENTRIES[name]():
            print(rep.render())
            if rep.verdict():
                bad = 1
    print()
    print('a FAILS line is a docstring that does not match the routine, not a '
          'routine that is broken.' if bad else 'every stated claim holds.')
    return bad


if __name__ == '__main__':
    sys.exit(main())
