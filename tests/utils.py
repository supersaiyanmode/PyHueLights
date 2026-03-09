from copy import deepcopy
from typing import Any

from pyhuelights.model import HueResource, Field, update_from_object, contains
from pyhuelights.network import BaseResourceManager, dict_parser


class SubSubResource(HueResource):
    FIELDS = [Field(obj_prop_name="test", validator=contains({1, 2, 3, 4, 5}))]

    def relative_url(self):
        return self.parent.relative_url() + "/sub"


class SubResource(HueResource):
    FIELDS = [
        Field(obj_prop_name="sub", writable=False),
        Field(obj_prop_name="sub2", cls=SubSubResource),
    ]

    def relative_url(self):
        return self.parent.relative_url() + "/sub"


class CustomResource(HueResource):
    FIELDS = [
        Field(obj_prop_name="id", is_key=True),
        Field(obj_prop_name="field1", writable=False),
        Field(obj_prop_name="field2", parse_json_name="f2"),
        Field(obj_prop_name="field3", cls=SubResource),
        Field(obj_prop_name="req", parse_json_name="request", parse=False),
    ]

    def relative_url(self):
        return "/parent/" + self.id


class CustomResourceManager(BaseResourceManager):

    async def get(self):
        obj = await self.make_request(relative_url="/res", method="get")
        return self.parse_response(obj, parser=dict_parser(CustomResource))

    async def put(self, resource):
        return await self.make_resource_update_request(resource)


class CustomResourceTestBase(object):
    DEFAULT_OBJ = {
        "field1": "blah",
        "f2": "hello",
        "field3": {
            "sub": "subval",
            "sub2": {
                "test": 1
            }
        }
    }

    def setup_method(self):
        self.obj = deepcopy(self.DEFAULT_OBJ)

    def get_resource(self, obj):
        self.resource = CustomResource()
        update_from_object(self.resource, "id", obj)
        return self.resource
