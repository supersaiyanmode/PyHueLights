import pytest

import highlight.registration
from highlight.core import HueApp, HueConnectionInfo
from highlight.exceptions import RegistrationFailed
from highlight.registration import register


class FakeResponse(object):
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.json = lambda : content


class FakeRequest(object):
    def __init__(self, responses):
        self.responses = responses

    def post(self, url, json):
        self.url = url
        self.json = json

        return self.responses.pop(0)

class TestRegistration(object):
    def setup_method(self):
        self.fake_request = FakeRequest([FakeResponse(200, {})]*30)
        self.backup_requests = highlight.registration.requests
        highlight.registration.requests = self.fake_request

    def teardown_method(self):
        highlight.registration.requests = self.backup_requests

    def test_username_in_store(self):
        assert register(None, None, {"username": "test"}) == "test"

    def test_registration_timeout(self):
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
