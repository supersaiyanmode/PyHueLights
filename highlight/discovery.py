"""
This module contains all the discovery method used to discover the Philips
Hue bridge on the current network.
"""


import requests

from .core import Bridge
from .exceptions import DiscoveryFailed


class BaseDiscovery(object):
    def discover(self):
        host = self.discover_host()
        self.validate_host(host)
        self.discovery_finished(host)
        return Bridge(host)

    def validate_host(self, host):
        print("Validating..")
        resp = requests.get("http://{}/description.xml".format(host))
        if resp.status_code != 200:
            raise DiscoveryFailed

        if "Philips" not in resp.text:
            raise DiscoveryFailed

    def discover_host(self):
        """ Needs to be overridden according to different discovery methods. """
        raise NotImplementedError

    def discovery_finished(self, host):
        pass


class NUPNPDiscovery(BaseDiscovery):
    """
    Uses NUPNP_URL below to discover the bridge as long as it is on the same
    network.
    """

    NUPNP_URL = "https://www.meethue.com/api/nupnp"

    def discover_host(self):
        try:
            obj = requests.get(self.NUPNP_URL).json()
        except requests.exceptions.RequestsWarning:
            raise DiscoveryFailed

        if not isinstance(obj, list) and len(obj) != 1:
            raise DiscoveryFailed
        try:
            return obj[0]['internalipaddress']
        except KeyError:
            raise DiscoveryFailed


class StaticHostDiscovery(BaseDiscovery):
    """
    Assumes the hostname 'philips-hue' and tries to connect.
    """

    def discover_host(self):
        return 'philips-hue'


class SSDPDiscovery(BaseDiscovery):
    """
    SSDP based discovery of the Hue bridge.
    """

    def discover_host(self):
        raise DiscoveryFailed


class DefaultDiscovery(object):
    """
    Discovery methods that tries all other discovery methods sequentially.
    """
    METHODS = [StaticHostDiscovery, NUPNPDiscovery, SSDPDiscovery]

    def discover(self):
        """ Tries all the discovery methods in self.METHODS. """
        for cls in self.METHODS:
            method = cls()
            try:
                return method.discover()
            except DiscoveryFailed:
                pass

        raise DiscoveryFailed
