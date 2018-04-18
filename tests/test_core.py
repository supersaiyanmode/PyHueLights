import requests_mock
import pytest

from highlight.core import HueResource, HueConnectionInfo
from highlight.manager import update_from_object


@pytest.fixture()
def mock_request():
    with requests_mock.Mocker() as mock:
        yield mock


class TestUpdateFromObject(object):
    class SubSubResource(HueResource):
        FIELDS = [
            {"name": "test"}
        ]

        def relative_url(self):
            return self.parent.relative_url() + "/sub"

    class SubResource(HueResource):
        FIELDS = [
            {"name": "sub", "readonly": True},
            {"name": "sub2"}
        ]

        def relative_url(self):
            return self.parent.relative_url() + "/sub"

    class CustomResource(HueResource):
        FIELDS = [
            {"name": "id", "field": "$KEY"},
            {"name": "field1", "readonly": True},
            {"name": "field2", "field": "f2"},
            {"name": "field3"},
        ]

        def relative_url(self):
            return "/parent/" + self.id

    CustomResource.FIELDS[-1]["cls"] = SubResource
    SubResource.FIELDS[-1]["cls"] = SubSubResource

    def test_update_from_object(self):
        obj = {
            "field1": "blah",
            "f2": "hello",
            "field3": {
                "sub": "subval",
                "sub2": {
                    "test": 1
                }
            }
        }

        resource = self.CustomResource()
        update_from_object(resource, "id", obj)

        assert resource.id == "id"
        assert resource.field1 == "blah"
        assert resource.field2 == "hello"
        assert isinstance(resource.field3, self.SubResource)
        assert resource.field3.sub == "subval"
        assert isinstance(resource.field3.sub2, self.SubSubResource)
        assert resource.field3.sub2.test == 1

    def test_update_from_string_instead_of_subobject(self):
        obj = {
            "f2": "hello",
            "field3": {
                "sub": "subval",
                "sub2": "subval2"
            }
        }

        resource = self.CustomResource()
        with pytest.raises(ValueError):
            update_from_object(resource, "id", obj)

    def test_update_from_bad_object(self):
        # "field1" is missing.
        obj = {
            "f2": "hello",
            "field3": {
                "sub": "subval",
                "sub2": {"test": 1}
            }
        }

        resource = self.CustomResource()
        with pytest.raises(ValueError):
            update_from_object(resource, "id", obj)

    def test_property_update(self):
        obj = {
            "field1": "blah",
            "f2": "hello",
            "field3": {
                "sub": "subval",
                "sub2": {"test": 1}
            }
        }

        resource = self.CustomResource()
        update_from_object(resource, "id", obj)

        resource.field2 = "world"
        resource.field3.sub2.test = 2

        assert resource.field2 == resource.field_field2 == "world"
        assert resource.field3.sub2.test == resource.field3.sub2.field_test == 2

        with pytest.raises(AttributeError):
            resource.field1 = "new-value"
        with pytest.raises(AttributeError):
            resource.field3 = self.SubResource(resource.connection_info)

        assert resource.dirty_flag == {"field2": True, "field3": True}
        assert resource.field3.dirty_flag == {"sub2": True}
        assert resource.field3.sub2.dirty_flag == {"test": True}

    def test_sub_resource_relative_url(self):
        obj = {
            "field1": "blah",
            "f2": "hello",
            "field3": {
                "sub": "subval",
                "sub2": {"test": 1}
            }
        }

        resource = self.CustomResource(HueConnectionInfo("h", "u"))
        update_from_object(resource, "id", obj)

        expected_url = "/parent/id/sub"
        assert resource.field3.relative_url() == expected_url
        assert resource.field3.sub2.relative_url() == expected_url + "/sub"
