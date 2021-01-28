import pytest

from pyhuelights.registration import AuthenticatedHueConnection
from pyhuelights.exceptions import RequestFailed
from pyhuelights.manager import construct_body, dict_parser

from utils import CustomResourceTestBase, CustomResource, RequestsTestsBase
from utils import CustomResourceManager, FakeResponse


class TestDictParser(CustomResourceTestBase):
    def test_parse(self):
        parser = dict_parser(CustomResource)
        res = parser({"1": self.obj})
        assert isinstance(res["1"], CustomResource)
        assert res["1"].id == "1"
        assert res["1"].field1 == "blah"


class TestConstructBody(CustomResourceTestBase):
    def test_construct_body(self):
        resource = self.get_resource(self.obj)

        resource.field3.sub2.test = 5

        res = construct_body(resource)
        expected = {
            "field3": {
                "sub2": {"test": 5}
            }
        }

        assert res == expected

    def test_construct_body_none(self):
        assert construct_body(None) is None


class TestBaseResourceManager(RequestsTestsBase):
    def test_invalid_api(self):
        conn = AuthenticatedHueConnection("", "")
        rm = CustomResourceManager(conn)

        with pytest.raises(AttributeError):
            rm.invalid_api()

    def test_simple_api(self):
        mock_response = {"1": self.DEFAULT_OBJ}
        self.fake_request.responses = [
            FakeResponse(200, mock_response)
        ]
        conn = AuthenticatedHueConnection("host", "user")
        rm = CustomResourceManager(conn)

        resp = rm.get()

        assert isinstance(resp["1"], CustomResource)
        assert len(self.fake_request.requests) == 1
        assert self.fake_request.requests == [
            ("http://host/api/user/res", None)
        ]

    def test_unexpected_response_status(self):
        self.fake_request.responses = [
            FakeResponse(500, {})
        ]
        conn = AuthenticatedHueConnection("host", "user")
        rm = CustomResourceManager(conn)

        with pytest.raises(RequestFailed):
            rm.get()

    def test_simple_update(self):
        mock_response = {"1": self.DEFAULT_OBJ}
        self.fake_request.responses = [
            FakeResponse(200, mock_response),
            FakeResponse(200, {})
        ]
        conn = AuthenticatedHueConnection("host", "user")
        rm = CustomResourceManager(conn)

        res = rm.get()['1']

        res.field2 = "world"
        res.field3.sub2.test = 5

        rm.put(res)

        assert len(self.fake_request.requests) == 2
        assert self.fake_request.requests[1] == \
            ("http://host/api/user/parent/1", {
                "f2": "world",
                "field3": {
                    "sub2": {"test": 5}
                }
            })
