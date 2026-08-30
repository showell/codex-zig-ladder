"""Grade a Codex numeric routine, and grade the claim its docstring makes.

Two customers built this by accident before it existed. `findings/atan/` graded
a Real arc tangent against zig's libm to four ULP, and `findings/cordic/` found
a docstring 5.4x optimistic without booting anything. They share almost no code
and every idea, so this is the shared half.

THE TWO THINGS BEING GRADED ARE DIFFERENT, and conflating them is the mistake
Cordic's docstring makes. There is what the routine COMPUTES, which is measured
against mathematical truth, and there is what its documentation CLAIMS, which is
a separate assertion that can be wrong on its own. A chapter whose numbers are
fine and whose docstring is off by 37x has one defect, not none.

AN ACCURACY FIGURE IS MEANINGLESS WITHOUT SAYING WHICH ACCURACY. Near a zero
crossing a small absolute error is a large fraction of a small value; near a
peak the reverse. Cordic's worst error is 0.54% of full scale AND 3.68%
relative -- the same measurement. So `Claim` carries a `reading`, and a claim
that does not say which reading it means cannot be checked, which is itself
reportable.
"""
import math, struct
from dataclasses import dataclass, field


def _bits(v):
    return struct.unpack('<q', struct.pack('<d', v))[0]


def ulps(a, b):
    """Distance in representable doubles, monotone across the sign."""
    ia, ib = _bits(a), _bits(b)
    if ia < 0: ia = -0x8000000000000000 - ia
    if ib < 0: ib = -0x8000000000000000 - ib
    return abs(ia - ib)


@dataclass
class Point:
    args: tuple
    got: float
    want: float

    @property
    def abs_err(self):
        return abs(self.got - self.want)

    @property
    def rel_err(self):
        return self.abs_err / abs(self.want) if self.want else None

    @property
    def ulp(self):
        return ulps(self.got, self.want)


@dataclass
class Claim:
    """What a docstring says, and under which reading it says it."""
    figure: float                      # e.g. 0.001 for "~0.1%"
    reading: str                       # 'absolute' | 'relative' | 'UNSTATED'
    scale: float = 1.0                 # full scale, for the absolute reading
    source: str = ''                   # where the claim is written


@dataclass
class Report:
    name: str
    points: list
    claim: Claim = None
    rel_floor: float = 0.0             # ignore relative error below this |want|
    validated: str = ''                # how the SUBJECT was shown faithful
    float_precision: bool = False      # is ULP a meaningful unit here?

    def worst(self, key):
        cands = [p for p in self.points if getattr(p, key) is not None]
        if key == 'rel_err':
            cands = [p for p in cands if abs(p.want) > self.rel_floor]
        return max(cands, key=lambda p: getattr(p, key)) if cands else None

    def within(self, tol, key='abs_err'):
        return sum(1 for p in self.points if getattr(p, key) is not None
                   and getattr(p, key) <= tol)

    def verdict(self):
        """None if the claim holds or there is none; else why it does not."""
        if not self.claim:
            return None
        c = self.claim
        wa, wr = self.worst('abs_err'), self.worst('rel_err')
        if c.reading == 'UNSTATED':
            return (f'the claim does not say WHICH accuracy. Absolute is '
                    f'{wa.abs_err / c.scale:.2%} of scale and relative is '
                    f'{wr.rel_err:.2%}; the claim of {c.figure:.2%} is '
                    f'{wa.abs_err / c.scale / c.figure:.1f}x off read one way '
                    f'and {wr.rel_err / c.figure:.0f}x the other')
        got = wa.abs_err / c.scale if c.reading == 'absolute' else wr.rel_err
        if got > c.figure:
            return (f'claimed {c.figure:.3%} {c.reading}, measured '
                    f'{got:.3%} -- {got / c.figure:.1f}x')
        return None

    def render(self):
        L = [f'== {self.name}: {len(self.points)} points']
        wa, wr = self.worst('abs_err'), self.worst('rel_err')
        if wa:
            L.append(f'   worst absolute {wa.abs_err:.4g}   at {wa.args}'
                     f'  (got {wa.got:.10g}, want {wa.want:.10g})')
        if wr:
            L.append(f'   worst relative {wr.rel_err:.3%}   at {wr.args}')
        # ULP compares two floats at float precision. Between an integer
        # fixed-point answer and a real it is a number in the quintillions and
        # means nothing, so it is printed only where it is a unit.
        if self.float_precision:
            wu = self.worst('ulp')
            if wu and wu.ulp:
                L.append(f'   worst ULP      {wu.ulp}   at {wu.args}')
        L.append(f'   subject validated: {self.validated}')
        if self.claim:
            v = self.verdict()
            L.append(f'   claim ({self.claim.source}): '
                     + ('HOLDS' if v is None else 'FAILS -- ' + v))
        return '\n'.join(L)


def grade(name, inputs, subject, reference, claim=None, rel_floor=0.0,
          validated=None, float_precision=False):
    """Run both sides over the SAME inputs and pair them by position.

    `subject` and `reference` are callables over one input tuple. Pairing by
    position is safe only because both are driven from this one list -- a rig
    whose two sides keep their own lists reports perfect agreement when they
    drift apart, because every row it compares is a row it built itself.
    """
    # A MODEL MUST SAY HOW IT WAS SHOWN FAITHFUL, and this refuses without it.
    # The Cordic model was validated twice before it was allowed to correct a
    # docstring -- against 18 values in the depot's own committed expectations,
    # and against bare metal on 20 angles. A transcription nobody checked
    # produces numbers indistinguishable from measurements, and the first
    # version of this catalog shipped exactly that for geo-sin before the
    # refusal existed.
    if not validated:
        raise SystemExit(
            f'{name}: grade() needs `validated=` -- one line saying how the '
            f'subject was shown to match the real implementation. A model '
            f'nobody checked reports numbers that look exactly like '
            f'measurements.')
    pts = []
    for a in inputs:
        args = a if isinstance(a, tuple) else (a,)
        pts.append(Point(args, float(subject(*args)), float(reference(*args))))
    return Report(name, pts, claim, rel_floor, validated, float_precision)
