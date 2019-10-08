"""
Numbers come from:
https://github.com/hsluv/hsluv-c/blob/498de4d9ce7a33933e9252fd3c87b75244215005/src/hsluv.c
I validated them against those generated by
https://github.com/colour-science/colour
By the way, thank you, mity!
https://github.com/hsluv/hsluv/issues/54#issuecomment-539325368
Only keep 17 significant digits, because if an IEEE 754 double-precision
number is converted to a decimal string with at least 17 significant
digits, and then converted back to double-precision representation, the
final result must match the original number.

Algorithms come from:
https://peteroupc.github.io/colorgen.html
http://brucelindbloom.com/
"""

from dataclasses import dataclass, astuple

__all__ = ('sRGB', 'CIEXYZ', 'CIELUV')


class Transform:
    def __init__(self, *args):
        self.matrix = args

    def __call__(self, *args):
        return tuple(sum(j * k for j, k in zip(i, args)) for i in self.matrix)


# noinspection PyPep8Naming
@dataclass(frozen=True)
class sRGB:
    R: float
    G: float
    B: float

    @staticmethod
    def compand(v):
        if v <= 0.0031308:
            return 12.92 * v
        else:
            return 1.055 * v ** (1 / 2.4) - 0.055

    @staticmethod
    def inverse_compand(v):
        if v > 0.04045:
            return ((v + 0.055) / 1.055) ** 2.4
        else:
            return v / 12.92

    @property
    def valid(self):
        return all(0 <= i <= 1 for i in astuple(self))

    @property
    def hex(self):
        return '#' + ''.join(f'{round(i * 255):02X}' for i in astuple(self))

    def CIEXYZ(self):
        t = Transform(
            (.41239079926595948, .35758433938387796, .18048078840183429),
            (.21263900587151036, .71516867876775593, .072192315360733715),
            (.019330818715591851, .11919477979462599, .95053215224966058),
        )
        return CIEXYZ(*t(*map(self.inverse_compand, astuple(self))))

    def CIELUV(self):
        return self.CIEXYZ().CIELUV()


# noinspection PyPep8Naming
@dataclass(frozen=True)
class CIEXYZ:
    X: float
    Y: float
    Z: float

    def sRGB(self):
        t = Transform(
            (3.2409699419045213, -1.5373831775700935, -.49861076029300328),
            (-.96924363628087983, 1.8759675015077207, .041555057407175612),
            (.055630079696993608, -.20397695888897656, 1.0569715142428786),
        )
        return sRGB(*map(sRGB.compand, t(*astuple(self))))

    def CIELUV(self):
        u_ref, v_ref = .19783000664283681, .46831999493879100
        epsilon, kappa = 216 / 24389, 24389 / 27
        if self.Y <= epsilon:
            L = kappa * self.Y
        else:
            L = 116 * self.Y ** (1 / 3) - 16
        if L == 0:
            return CIELUV(0, 0, 0)
        divider = self.X + 15 * self.Y + 3 * self.Z
        u = 13 * L * (4 * self.X / divider - u_ref)
        v = 13 * L * (9 * self.Y / divider - v_ref)
        return CIELUV(L, u, v)


# noinspection PyPep8Naming
@dataclass(frozen=True)
class CIELUV:
    L: float
    u: float
    v: float

    def CIEXYZ(self):
        u_ref, v_ref = .19783000664283681, .46831999493879100
        epsilon, kappa = 216 / 24389, 24389 / 27
        if self.L == 0:
            return CIEXYZ(0, 0, 0)
        if self.L > kappa * epsilon:
            Y = ((self.L + 16) / 116) ** 3
        else:
            Y = self.L / kappa
        u_ = self.u + 13 * self.L * u_ref
        v_ = self.v + 13 * self.L * v_ref
        X = 2.25 * Y * u_ / v_
        Z = 39 * Y * self.L / v_ - X / 3 - 5 * Y
        return CIEXYZ(X, Y, Z)

    def sRGB(self):
        return self.CIEXYZ().sRGB()