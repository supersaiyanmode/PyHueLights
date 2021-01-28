import pytest

from pyhuelights.core import HueApp
from pyhuelights.exceptions import RegistrationFailed
from pyhuelights.registration import register, AuthenticatedHueConnection
from pyhuelights.discovery import UnauthenticatedHueRawConnectionInfo as Raw

from utils import RequestsTestsBase, FakeResponse


class TestRegistration(RequestsTestsBase):
    def test_username_in_store(self):
        store = {"username": "test"}
        assert register(Raw(""), None, store).username == "test"

    def test_registration_timeout(self):
        self.fake_request.responses = [FakeResponse(200, {})] * 30
        with pytest.raises(RegistrationFailed):
            register(Raw(""), HueApp("", ""), {}, 5)

    def test_bad_response(self):
        self.fake_request.responses = [FakeResponse(500, {})]

        with pytest.raises(RegistrationFailed):
            register(Raw(""), HueApp("", ""), {}, 30)

    def test_unexpected_response(self):
        self.fake_request.responses = [FakeResponse(200, {})] * 3

        with pytest.raises(RegistrationFailed):
            register(Raw(""), HueApp("", ""), {}, 2)

    def test_sucessful_registration(self):
        self.fake_request.responses = [
            FakeResponse(200, {}),
            FakeResponse(200, {}),
            FakeResponse(200, [{"success": {"username": "abc"}}])
        ]

        store = {}
        assert register(Raw(""), HueApp("", ""), store).username == "abc"
        assert store == {"username": "abc"}
