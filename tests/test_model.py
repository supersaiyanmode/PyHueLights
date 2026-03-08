from copy import deepcopy
import pytest

from pyhuelights.model import EMPTY, update_from_object, Light as LightRaw
from pyhuelights.core import Temperature
from pyhuelights.network import construct_body

from utils import CustomResourceTestBase, SubResource, SubSubResource


class TestUpdateFromObject(CustomResourceTestBase):

    def test_update_from_object(self):
        resource = self.get_resource(self.obj)

        assert resource.id == "id"
        assert resource.field1 == "blah"
        assert resource.field2 == "hello"
        assert isinstance(resource.field3, SubResource)
        assert resource.field3.sub == "subval"
        assert isinstance(resource.field3.sub2, SubSubResource)
        assert resource.field3.sub2.test == 1

    def test_update_from_string_instead_of_subobject(self):
        self.obj["field3"]["sub2"] = "subval2"

        with pytest.raises(ValueError):
            self.get_resource(self.obj)

    def test_update_from_bad_object(self):
        # "field1" is not optional.
        del self.obj["field1"]

        with pytest.raises(ValueError):
            self.get_resource(self.obj)

    def test_property_update(self):
        resource = self.get_resource(self.obj)

        resource.field2 = "world"
        resource.field3.sub2.test = 2

        assert resource.field2 == "world"
        assert resource.field3.sub2.test == 2

        with pytest.raises(AttributeError):
            resource.field1 = "new-value"
        with pytest.raises(AttributeError):
            resource.field3 = None

        assert resource.dirty_flag == {
            "field2": True,
            "field3": True,
            "req": False,
            "field1": False
        }
        assert resource.field3.dirty_flag == {"sub2": True, "sub": False}
        assert resource.field3.sub2.dirty_flag == {"test": True}

    def test_property_update_invalid_value(self):
        resource = self.get_resource(self.obj)

        resource.field3.sub2.test = 4

        with pytest.raises(ValueError):
            resource.field3.sub2.test = 10  # [1,5] are valid values.

    def test_sub_resource_relative_url(self):
        resource = self.get_resource(self.obj)

        expected_url = "/parent/id/sub"
        assert resource.field3.relative_url() == expected_url
        assert resource.field3.sub2.relative_url() == expected_url + "/sub"

    def test_reset_dirty(self):
        resource = self.get_resource(self.obj)

        assert not any(resource.dirty_flag.values())

        resource.field2 = "world"
        resource.field3.sub2.test = 2

        assert {k
                for k, v in resource.dirty_flag.items()
                if v} == {"field2", "field3"}
        assert resource.field3.dirty_flag == {"sub2": True, "sub": False}
        assert resource.field3.sub2.dirty_flag == {"test": True}

        resource.reset()

        assert not any(resource.dirty_flag.values())
        assert resource.field3.dirty_flag == {"sub": False, "sub2": False}
        assert resource.field3.sub2.dirty_flag == {"test": False}

        assert resource.field2 == "hello"
        assert resource.field3.sub2.test == 1

    def test_commit(self):
        resource = self.get_resource(self.obj)

        resource.field2 = "world"
        resource.field3.sub2.test = 2

        resource.commit()

        assert not any(resource.dirty_flag.values())
        assert resource.field3.dirty_flag == {"sub": False, "sub2": False}
        assert resource.field3.sub2.dirty_flag == {"test": False}

        assert resource.field2 == "world"

        resource.reset()

        assert resource.field2 == "world"
        assert resource.field3.sub2.test == 2


class TestInitObject(CustomResourceTestBase):

    def test_non_parsed_field_dirty(self):
        resource = self.get_resource(self.obj)

        assert resource.req is EMPTY

        resource.req = "test"

        assert resource.req == "test"
        assert resource.dirty_flag["req"] == True
        assert resource.property_to_json_key_map["req"] == "request"

    def test_reset_dirty(self):
        resource = self.get_resource(self.obj)
        resource.req = "test"

        resource.reset()

        assert resource.req is EMPTY


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


class TestLightRaw:

    def test_light_parse(self):
        light = LightRaw()
        obj = deepcopy(LIGHT_JSON)
        obj["state"]["ct"] = 153
        update_from_object(light, "id", obj)
        assert light.id == "id"
        assert light.state.temperature == 6500

        obj["state"]["ct"] = 500
        update_from_object(light, "id", obj)
        assert light.state.temperature == 2000

    def test_light_set_temperature_conversion(self):
        from pyhuelights.core import Light
        light_model = LightRaw()
        update_from_object(light_model, "id", LIGHT_JSON)
        light = Light(light_model)

        light.color = Temperature(2000)
        assert construct_body(light_model) == {
            'state': {
                'colormode': 'ct',
                'ct': 500
            }
        }

        light.color = Temperature(6500)
        assert construct_body(light_model) == {
            'state': {
                'colormode': 'ct',
                'ct': 153
            }
        }
