import requests_mock
import pytest

from highlight.core import HueResource, HueConnectionInfo


@pytest.fixture()
def mock_request():
    with requests_mock.Mocker() as mock:
        yield mock


class TestHueResource(object):
    class CustomResource(HueResource):
        FIELDS = [
            {"name": "field1", "readonly": True},
            {"name": "field2", "field": "f2"},
        ]

    def test_update_from_object(self):
        obj = {
            "field1": "blah",
            "f2": "hello",
        }

        resource = self.CustomResource(HueConnectionInfo("h", "u"), "r")
        resource.update_from_object(obj)

        assert resource.field1 == resource.field_field1 == "blah"
        assert resource.field2 == resource.field_field2 == "hello"

    def test_property_update(self):
        obj = {
            "field1": "blah",
            "f2": "hello",
        }

        resource = self.CustomResource(HueConnectionInfo("h", "u"), "r")
        resource.update_from_object(obj)

        resource.field2 = "world"
        assert resource.field2 == resource.field_field2 == "world"

        with pytest.raises(AttributeError):
            resource.field1 = "new-value"

        assert resource.dirty_flag == {"field2": True}
