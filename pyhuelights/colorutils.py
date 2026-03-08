import math
from typing import Tuple


def rgb_to_xy(r: int, g: int, b: int) -> Tuple[float, float]:
    """ Standard sRGB to XYZ (D65) transformation. """

    def enhance_color(normalized):
        if normalized > 0.04045:
            return math.pow((normalized + 0.055) / (1.0 + 0.055), 2.4)
        else:
            return normalized / 12.92

    r_e = enhance_color(r / 255.0)
    g_e = enhance_color(g / 255.0)
    b_e = enhance_color(b / 255.0)

    # Standard sRGB to XYZ matrix (D65).
    X = r_e * 0.4124 + g_e * 0.3576 + b_e * 0.1805
    Y = r_e * 0.2126 + g_e * 0.7152 + b_e * 0.0722
    Z = r_e * 0.0193 + g_e * 0.1192 + b_e * 0.9505

    if X + Y + Z == 0:
        return 0.0, 0.0
    else:
        return X / (X + Y + Z), Y / (X + Y + Z)


def xy_to_rgb(x: float, y: float, bri: int = 255) -> Tuple[int, int, int]:
    """ XYZ to sRGB transformation. """
    if bri == 0 or y == 0:
        return 0, 0, 0

    # XYZ from xyY coordinates.
    Y = bri / 255.0
    X = (Y / y) * x
    Z = (Y / y) * (1.0 - x - y)

    # Standard XYZ to sRGB matrix (D65).
    r = X * 3.2406 - Y * 1.5372 - Z * 0.4986
    g = -X * 0.9689 + Y * 1.8758 + Z * 0.0415
    b = X * 0.0557 - Y * 0.2040 + Z * 1.0570

    # Inverse gamma correction.
    def reverse_enhance_color(normalized):
        if normalized <= 0.0031308:
            return normalized * 12.92
        else:
            return (1.0 + 0.055) * math.pow(normalized, (1.0 / 2.4)) - 0.055

    r = reverse_enhance_color(r)
    g = reverse_enhance_color(g)
    b = reverse_enhance_color(b)

    # Scaling to handle out-of-gamut values.
    max_val = max(r, g, b)
    if max_val > 1.0:
        r /= max_val
        g /= max_val
        b /= max_val

    # Clip to [0, 1] before scaling to 0-255.
    r = max(0, min(1, r))
    g = max(0, min(1, g))
    b = max(0, min(1, b))

    return int(r * 255), int(g * 255), int(b * 255)
