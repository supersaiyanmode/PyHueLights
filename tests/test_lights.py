from copy import deepcopy
import pytest

from pyhuelights.core import update_from_object, Light, Color
from pyhuelights.manager import construct_body

LIGHT_JSON = {
    "state": {
        "on": False,
        "bri": 254,
        "hue": 13248,
        "sat": 5,
        "effect": "none",
        "xy": [0.3812, 0.3793],
        "ct": 250,
        "alert": "select",
        "colormode": "ct",
        "mode": "homeautomation",
        "reachable": False
    },
    "name": "Dining Room Striplight 1",
    "capabilities": {
        "control": {
            "mindimlevel": 40,
            "maxlumen": 1600,
            "colorgamuttype": "C",
            "colorgamut": [[0.6915, 0.3083], [0.17, 0.7], [0.1532, 0.0475]],
            "ct": {
                "min": 153,
                "max": 500
            }
        },
    },
    "uniqueid": "00:17:88:01:04:05:09:f7-0b",
    "swversion": "1.116.3",
    "swconfigid": "E88CA42C",
    "productid": "Philips-LST002-1-LedStripsv3",
    "type": "Color temperature light",
    "modelid": "LTD008"
}


class TestLights:

    def test_light_parse(self):
        light = Light()
        obj = deepcopy(LIGHT_JSON)
        obj["state"]["ct"] = 153
        update_from_object(light, "id", obj)
        assert light.id == "id"
        assert light.state.temperature == 6500

        obj["state"]["ct"] = 500
        update_from_object(light, "id", obj)
        assert light.state.temperature == 2000

    def test_light_set_temperature_conversion(self):
        light = Light()
        update_from_object(light, "id", LIGHT_JSON)

        light.state.set_color(Color.from_kelvin(2000))
        assert construct_body(light) == {
            'state': {
                'colormode': 'ct',
                'ct': 500
            }
        }

        light.state.set_color(Color.from_kelvin(6500))
        assert construct_body(light) == {
            'state': {
                'colormode': 'ct',
                'ct': 153
            }
        }
