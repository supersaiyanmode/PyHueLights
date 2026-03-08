import pytest
from pyhuelights.core import Light, Temperature, HueSat, RGB
from pyhuelights.colorutils import rgb_to_xy, xy_to_rgb
from pyhuelights.model import Light as LightRaw, update_from_object


def test_lights_abstraction():
    light_model = LightRaw()
    # Initialize with some data.
    data = {
        "state": {
            "on": True,
            "bri": 100,
            "colormode": "xy",
            "xy": [0.4, 0.4],
            "ct": 250,
            "hue": 1000,
            "sat": 100,
            "reachable": True
        },
        "capabilities": {
            "control": {}
        },
        "name": "Test Light",
        "type": "Extended color light",
        "modelid": "LCT001",
        "swversion": "65003148",
        "uniqueid": "00:17:88:01:00:bc:c6:12-0b"
    }
    update_from_object(light_model, "1", data)

    light_obj = Light(light_model)

    # Test brightness.
    assert light_obj.brightness == 100
    light_obj.brightness = 200
    assert light_model.state.brightness == 200
    assert light_model.dirty_flag["state"] is True

    # Test color (xy mode initially returns RGB in my current implementation).
    assert isinstance(light_obj.color, RGB)

    # Change color to temperature.
    new_color = Temperature(3000)
    light_obj.color = new_color
    assert light_model.state.temperature == 3000
    assert light_model.state.color_mode == 'ct'

    # Test color (ct mode).
    assert isinstance(light_obj.color, Temperature)
    assert light_obj.color.value == 3000

    # Change color to HueSat.
    new_hs = HueSat(10000, 200)
    light_obj.color = new_hs
    assert light_model.state.hue == 10000
    assert light_model.state.saturation == 200
    assert light_model.state.color_mode == 'hs'
    assert isinstance(light_obj.color, HueSat)


def test_rgb_to_xy_to_rgb():
    # Test a broad range of colors to ensure accuracy of transformations.
    colors = [
        (255, 0, 0),    # Pure Red
        (0, 255, 0),    # Pure Green
        (0, 0, 255),    # Pure Blue
        (255, 255, 255), # Pure White
        (128, 128, 128), # Mid Grey
        (255, 255, 0),  # Yellow
        (0, 255, 255),  # Cyan
        (255, 0, 255),  # Magenta
        (255, 165, 0),  # Orange
        (128, 0, 128),  # Purple
        (255, 192, 203), # Pink
        (165, 42, 42),  # Brown
        (0, 128, 128),  # Teal
        (128, 128, 0),  # Olive
        (0, 0, 128),    # Navy
        (250, 235, 215), # Antique White
        (230, 230, 250), # Lavender
        (245, 245, 220), # Beige
        (0, 255, 127),  # Spring Green
        (75, 0, 130),   # Indigo
        (255, 127, 80),  # Coral
        (64, 224, 208), # Turquoise
        (218, 165, 32), # Goldenrod
        (47, 79, 79),   # Dark Slate Grey
        (255, 250, 205), # Lemon Chiffon
    ]

    for r, g, b in colors:
        x, y = rgb_to_xy(r, g, b)

        # Calculate Y for the roundtrip based on core.py's sRGB to XYZ matrix.
        def enhance_color(normalized):
            if normalized > 0.04045:
                return ((normalized + 0.055) / (1.0 + 0.055)) ** 2.4
            else:
                return normalized / 12.92

        rn = enhance_color(r / 255.0)
        gn = enhance_color(g / 255.0)
        bn = enhance_color(b / 255.0)

        # Standard luminance (Y) calculation using sRGB coefficients.
        Y = rn * 0.2126 + gn * 0.7152 + bn * 0.0722
        bri = Y * 255.0

        r2, g2, b2 = xy_to_rgb(x, y, bri=int(bri))

        # We allow a small tolerance for precision and gamut clipping.
        assert r2 == pytest.approx(r, abs=20)
        assert g2 == pytest.approx(g, abs=20)
        assert b2 == pytest.approx(b, abs=20)


def test_xy_to_rgb_boundaries():
    # Test boundary cases.
    assert xy_to_rgb(0.0, 0.0) == (0, 0, 0)
    assert xy_to_rgb(0.5, 0.5, bri=0) == (0, 0, 0)


def test_grayscale():
    # Grayscale colors should have the same x, y coordinates for different brightness levels.
    for i in range(16, 256, 16):
        x, y = rgb_to_xy(i, i, i)
        assert x == pytest.approx(0.3127, abs=0.01)
        assert y == pytest.approx(0.3290, abs=0.01)


def test_validation():
    with pytest.raises(ValueError):
        Temperature(1000)
    with pytest.raises(ValueError):
        Temperature(7000)
    with pytest.raises(ValueError):
        HueSat(-1, 100)
    with pytest.raises(ValueError):
        HueSat(70000, 100)
    with pytest.raises(ValueError):
        HueSat(100, 300)
    with pytest.raises(ValueError):
        RGB(-1, 0, 0)
    with pytest.raises(ValueError):
        RGB(256, 0, 0)
