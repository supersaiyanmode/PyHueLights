import requests_mock
import pytest

from highlight.core import HueResource, HueConnectionInfo


@pytest.fixture()
def mock_request():
    with requests_mock.Mocker() as mock:
        yield mock


class TestHueResource(object):
    class SubResource(HueResource):
        FIELDS = [
            {"name": "sub", "readonly": True},
            {"name": "sub2"}
        ]

        def format_url(self):
            return self.parent.format_url() + "/sub"

    class CustomResource(HueResource):
        FIELDS = [
            {"name": "field1", "readonly": True},
            {"name": "field2", "field": "f2"},
            {"name": "field3"},
        ]

        def format_url(self):
            return super(TestHueResource.CustomResource, self).format_url() +\
                  "/parent"

    CustomResource.FIELDS[-1]["cls"] = SubResource

    def test_update_from_object(self):
        obj = {
            "field1": "blah",
            "f2": "hello",
            "field3": {
                "sub": "subval",
                "sub2": "subval2"
            }
        }

        resource = self.CustomResource(HueConnectionInfo("h", "u"))
        resource.update_from_object(obj)

        assert resource.field1 == resource.field_field1 == "blah"
        assert resource.field2 == resource.field_field2 == "hello"

    def test_property_update(self):
        obj = {
            "field1": "blah",
            "f2": "hello",
            "field3": {
                "sub": "subval",
                "sub2": "subval2"
            }
        }

        resource = self.CustomResource(HueConnectionInfo("h", "u"))
        resource.update_from_object(obj)

        resource.field2 = "world"
        assert resource.field2 == resource.field_field2 == "world"

        with pytest.raises(AttributeError):
            resource.field1 = "new-value"
        with pytest.raises(AttributeError):
            resource.field3 = self.SubResource(resource.connection_info)

        assert resource.dirty_flag == {"field2": True}

    def test_sub_resource_format_url(self):
        obj = {
            "field1": "blah",
            "f2": "hello",
            "field3": {
                "sub": "subval",
                "sub2": "subval2"
            }
        }

        resource = self.CustomResource(HueConnectionInfo("h", "u"))
        resource.update_from_object(obj)

        expected_url = "http://h/api/u/parent/sub"
        assert resource.field3.format_url() == expected_url

    def test_sub_resource_parse(self):
        obj = {
            "field1": "blah",
            "f2": "hello",
            "field3": {
                "sub": "subval",
                "sub2": "subval2"
            }
        }

        resource = self.CustomResource(HueConnectionInfo("h", "u"))
        resource.update_from_object(obj)

        assert isinstance(resource.field3, self.SubResource)
