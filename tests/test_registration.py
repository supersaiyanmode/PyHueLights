import pytest

from pyhuelights.core import HueApp, HueConnectionInfo
from pyhuelights.exceptions import RegistrationFailed
from pyhuelights.registration import register

from utils import RequestsTestsBase, FakeResponse


class TestRegistration(RequestsTestsBase):
    def test_username_in_store(self):
        store = {"username": "test"}
        assert register(HueConnectionInfo(""), None, store) == "test"

    def test_registration_timeout(self):
        self.fake_request.responses = [FakeResponse(200, {})] * 30
        with pytest.raises(RegistrationFailed):
            register(HueConnectionInfo(""), HueApp("", ""), {}, 5)

    def test_bad_response(self):
        self.fake_request.responses = [FakeResponse(500, {})]

        with pytest.raises(RegistrationFailed):
            register(HueConnectionInfo(""), HueApp("", ""), {}, 30)

    def test_unexpected_response(self):
        self.fake_request.responses = [FakeResponse(200, {})] * 3

        with pytest.raises(RegistrationFailed):
            register(HueConnectionInfo(""), HueApp("", ""), {}, 2)

    def test_sucessful_registration(self):
        self.fake_request.responses = [
            FakeResponse(200, {}),
            FakeResponse(200, {}),
            FakeResponse(200, [{"success": {"username": "abc"}}])
        ]

        store = {}
        assert register(HueConnectionInfo(""), HueApp("", ""), store) == "abc"
        assert store == {"username": "abc"}
