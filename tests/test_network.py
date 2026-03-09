import json
import pytest
import respx
from httpx import Response

from pyhuelights.registration import AuthenticatedHueConnection
from pyhuelights.exceptions import RequestFailed
from pyhuelights.network import construct_body, dict_parser

from utils import CustomResourceTestBase, CustomResource
from utils import CustomResourceManager


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
        expected = {"field3": {"sub2": {"test": 5}}}

        assert res == expected

    def test_construct_body_none(self):
        assert construct_body(None) is None


class TestBaseResourceManager(CustomResourceTestBase):

    @pytest.mark.asyncio
    async def test_invalid_api(self):
        conn = AuthenticatedHueConnection("", "")
        rm = CustomResourceManager(conn)

        with pytest.raises(AttributeError):
            rm.invalid_api()

    @pytest.mark.asyncio
    @respx.mock
    async def test_simple_api(self):
        mock_response = {"1": self.DEFAULT_OBJ}
        respx.get("http://host/api/user/res").mock(
            return_value=Response(200, json=mock_response))

        conn = AuthenticatedHueConnection("host", "user")
        rm = CustomResourceManager(conn)

        resp = await rm.get()

        assert isinstance(resp["1"], CustomResource)

    @pytest.mark.asyncio
    @respx.mock
    async def test_unexpected_response_status(self):
        respx.get("http://host/api/user/res").mock(return_value=Response(500))

        conn = AuthenticatedHueConnection("host", "user")
        rm = CustomResourceManager(conn)

        with pytest.raises(RequestFailed):
            await rm.get()

    @pytest.mark.asyncio
    @respx.mock
    async def test_simple_update(self):
        mock_response = {"1": self.DEFAULT_OBJ}
        respx.get("http://host/api/user/res").mock(
            return_value=Response(200, json=mock_response))
        update_route = respx.put("http://host/api/user/parent/1").mock(
            return_value=Response(200, json={}))

        conn = AuthenticatedHueConnection("host", "user")
        rm = CustomResourceManager(conn)

        resp = await rm.get()
        res = resp['1']

        res.field2 = "world"
        res.field3.sub2.test = 5

        await rm.put(res)

        assert update_route.called
        assert json.loads(update_route.calls.last.request.content) == {
            "f2": "world",
            "field3": {
                "sub2": {
                    "test": 5
                }
            }
        }
