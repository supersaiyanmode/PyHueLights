
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


class TestDefaultDiscovery(object):
    def test_static_host(self, mock_request):
        mock_request.get("http://philips-hue/description.xml", text="Philips")

        discovery = DefaultDiscovery()
        connection_info = discovery.discover()

        assert connection_info.host == 'philips-hue'

    def test_nupnp_discovery(self, mock_request):
        mock_request.get("http://philips-hue/description.xml", status_code=404)
        data = {"internalipaddress": "ip"}
        mock_request.get(NUPNPDiscovery.NUPNP_URL, json=[data])
        mock_request.get("http://ip/description.xml", text="Philips")

        discovery = DefaultDiscovery()
        connection_info = discovery.discover()

        assert connection_info.host == 'ip'

    def test_all_methods_failed(self, mock_request):
        mock_request.get("http://philips-hue/description.xml", status_code=404)
        mock_request.get(NUPNPDiscovery.NUPNP_URL, status_code=404)

        with pytest.raises(DiscoveryFailed):
            DefaultDiscovery().discover()
