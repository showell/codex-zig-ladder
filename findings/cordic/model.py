"""A faithful Python model of Math chapter Cordic's rotation mode.

Transcribed from codex/foreword/math/Cordic.codex, not from the CORDIC
literature: the point is to grade THIS implementation, so every fixed-point
division and the truncated angle table are reproduced exactly. Codex Integer
division truncates toward zero (idiv), which Python's // does not.
"""
import math

SCALE, ITERS, GAIN = 1000, 16, 607
ATAN = [785, 463, 244, 124, 62, 31, 15, 7, 3, 1, 0, 0, 0, 0, 0, 0]
HALF_PI, PI, THREE_HALF_PI, TWO_PI = 1571, 3142, 4712, 6283


def idiv(a, b):
    """Truncate toward zero, as idiv does and as Python's // does not."""
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def rotate(target, x, y, i):
    while i < ITERS:
        a = ATAN[i]
        step = 1 << i
        if target > 0:
            target, x, y = target - a, x - idiv(y, step), y + idiv(x, step)
        else:
            target, x, y = target + a, x + idiv(y, step), y - idiv(x, step)
        i += 1
    return idiv(x * GAIN, SCALE), idiv(y * GAIN, SCALE)


def normalize(a):
    a2 = a - idiv(a, TWO_PI) * TWO_PI
    return a2 + TWO_PI if a2 < 0 else a2


def sincos(angle_milli):
    a = normalize(angle_milli)
    if a <= HALF_PI:
        return rotate(a, SCALE, 0, 0)
    if a <= PI:
        c, s = rotate(PI - a, SCALE, 0, 0)
        return -c, s
    if a <= THREE_HALF_PI:
        c, s = rotate(a - PI, SCALE, 0, 0)
        return -c, -s
    c, s = rotate(TWO_PI - a, SCALE, 0, 0)
    return c, -s


def true_sincos(angle_milli):
    r = angle_milli / SCALE
    return math.cos(r) * SCALE, math.sin(r) * SCALE
