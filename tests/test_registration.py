import pytest
import respx
from httpx import Response

from pyhuelights.model import HueApp
from pyhuelights.exceptions import RegistrationFailed
from pyhuelights.registration import register
from pyhuelights.discovery import UnauthenticatedHueRawConnectionInfo as Raw


class TestRegistration:

    @pytest.mark.asyncio
    async def test_username_in_store(self):
        store = {"username": "test"}
        res = await register(Raw(""), None, store)
        assert res.username == "test"

    @pytest.mark.asyncio
    @respx.mock
    async def test_registration_timeout(self):
        respx.post("http://host/api").mock(
            return_value=Response(200, json=[{}]))

        with pytest.raises(RegistrationFailed):
            await register(Raw("host"), HueApp("app", "client"), {}, 0.1)

    @pytest.mark.asyncio
    @respx.mock
    async def test_bad_response(self):
        respx.post("http://host/api").mock(return_value=Response(500))

        with pytest.raises(RegistrationFailed):
            await register(Raw("host"), HueApp("app", "client"), {}, 30)

    @pytest.mark.asyncio
    @respx.mock
    async def test_sucessful_registration(self):
        respx.post("http://host/api").side_effect = [
            Response(200, json=[{}]),
            Response(200, json=[{
                "success": {
                    "username": "abc"
                }
            }])
        ]

        store = {}
        res = await register(Raw("host"), HueApp("app", "client"), store)
        assert res.username == "abc"
        assert store == {"username": "abc"}
