
import pytest
import requests_mock

from pyhuelights.discovery import NUPNPDiscovery, StaticHostDiscovery
from pyhuelights.discovery import DefaultDiscovery
from pyhuelights.exceptions import DiscoveryFailed


@pytest.fixture()
def mock_request():
    with requests_mock.Mocker() as mock:
        yield mock


class TestNUPNPDiscovery(object):
    def test_discovery_failed_request_exception(self, mock_request):
        mock_request.get(NUPNPDiscovery.NUPNP_URL, status_code=400)

        with pytest.raises(DiscoveryFailed):
            NUPNPDiscovery().discover_host()

    def test_not_a_json_response(self, mock_request):
        mock_request.get(NUPNPDiscovery.NUPNP_URL, text='not-json')

        with pytest.raises(DiscoveryFailed):
            NUPNPDiscovery().discover_host()

    def test_bad_json_response(self, mock_request):
        mock_request.get(NUPNPDiscovery.NUPNP_URL, json={})

        with pytest.raises(DiscoveryFailed):
            NUPNPDiscovery().discover_host()

    def test_multiple_hosts_discovered(self, mock_request):
        mock_request.get(NUPNPDiscovery.NUPNP_URL, json=[{}, {}])

        with pytest.raises(DiscoveryFailed):
            NUPNPDiscovery().discover_host()

    def test_bad_host_info(self, mock_request):
        mock_request.get(NUPNPDiscovery.NUPNP_URL, json=[{"key": "value"}])

        with pytest.raises(DiscoveryFailed):
            NUPNPDiscovery().discover_host()

    def test_discovery(self, mock_request):
        data = {"internalipaddress": "ip"}
        mock_request.get(NUPNPDiscovery.NUPNP_URL, json=[data])
        mock_request.get("http://ip/description.xml", text="Philips")

        assert "ip" == NUPNPDiscovery().discover_host()


class TestStaticHostDiscovery(object):
    def test_discover_host(self):
        assert "philips-hue" == StaticHostDiscovery().discover_host()

