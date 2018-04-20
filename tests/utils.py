from copy import deepcopy

from highlight.core import HueResource, update_from_object


class SubSubResource(HueResource):
    FIELDS = [
        {"name": "test", "values": [1, 2, 3, 4, 5]}
    ]

    def relative_url(self):
        return self.parent.relative_url() + "/sub"


class SubResource(HueResource):
    FIELDS = [
        {"name": "sub", "readonly": True},
        {"name": "sub2", "cls": SubSubResource}
    ]

    def relative_url(self):
        return self.parent.relative_url() + "/sub"


class CustomResource(HueResource):
    FIELDS = [
        {"name": "id", "field": "$KEY"},
        {"name": "field1", "readonly": True},
        {"name": "field2", "field": "f2"},
        {"name": "field3", "cls": SubResource},
    ]

    def relative_url(self):
        return "/parent/" + self.id


class CustomResourceTestBase(object):
    DEFAULT_OBJ = {
        "field1": "blah",
        "f2": "hello",
        "field3": {
            "sub": "subval",
            "sub2": {"test": 1}
        }
    }

    def setup_method(self):
        self.obj = deepcopy(self.DEFAULT_OBJ)

    def get_resource(self, obj):
        self.resource = CustomResource()
        update_from_object(self.resource, "id", obj)
        return self.resource
