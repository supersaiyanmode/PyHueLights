from copy import deepcopy

import requests

from pyhuelights.core import HueResource, Field, update_from_object
from pyhuelights.manager import BaseResourceManager, dict_parser


class FakeResponse(object):
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.json = lambda : content
        self.text = content


class FakeRequest(object):
    def __init__(self, responses):
        self.responses = responses
        self.requests = []

    def post(self, url, json=None):
        self.requests.append((url, json))

        return self.responses.pop(0)

    put = post
    get = post


class SubSubResource(HueResource):
    FIELDS = [
        Field(obj_prop_name="test", values=[1, 2, 3, 4, 5])
    ]

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
    def get(self):
        obj = self.make_request(relative_url="/res", method="get")
        return self.parse_response(obj, parser=dict_parser(CustomResource))

    def put(self, resource):
        return self.make_resource_update_request(resource)


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


class RequestsTestsBase(object):
    DEFAULT_OBJ = {
        "field1": "blah",
        "f2": "hello",
        "field3": {
            "sub": "subval",
            "sub2": {"test": 1}
        }
    }

    def setup_method(self):
        self.fake_request = FakeRequest([])
        self.backup_requests = requests.get, requests.put, requests.post
        requests.put = self.fake_request.put
        requests.get = self.fake_request.get
        requests.post = self.fake_request.post

    def teardown_method(self):
        requests.put, requests.get, requests.post = self.backup_requests
