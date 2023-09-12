"""
This module contains all the discovery method used to discover the Philips
Hue bridge on the current network.
"""

import socket
import time
import threading

import requests

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

from .exceptions import DiscoveryFailed

class MDNSListener(ServiceListener):
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback

    def add_service(self, zc, typ, name) -> None:
        info = zc.get_service_info(typ, name)
        self.callback(info)

    def remove_service(self, zc, type_, name) -> None:
        pass

    def update_service(self, zc, type_, name) -> None:
        pass


class UnauthenticatedHueRawConnectionInfo(object):
    """ Represents the result of a Hue Bridge discovery. """
    def __init__(self, host):
        self.host = host

    def validate(self):
        try:
            resp = requests.get("http://{}/description.xml".format(self.host))
            if resp.status_code != 200:
                return False
        except IOError:
            return False

        return "Philips" in resp.text


class BaseDiscovery(object):
    def discover(self):
        host = self.discover_host()
        connection_info = self.validate_host(host)
        return self.discovery_finished(connection_info)

    def validate_host(self, host):
        connection_info = UnauthenticatedHueRawConnectionInfo(host)

        if not connection_info.validate():
            raise DiscoveryFailed

        return connection_info

    def discover_host(self):
        """ Needs to be overridden according to different discovery methods. """
        raise NotImplementedError

    def discovery_finished(self, connection_info):
        return connection_info


class NUPNPDiscovery(BaseDiscovery):
    """
    Uses NUPNP_URL below to discover the bridge as long as it is on the same
    network.
    """

    NUPNP_URL = "https://discovery.meethue.com"

    def discover_host(self):
        try:
            obj = requests.get(self.NUPNP_URL).json()
        except requests.exceptions.RequestException:
            raise DiscoveryFailed
        except ValueError:
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


class MDNSDiscovery(BaseDiscovery):
    """
    MDNS based discovery of the Hue bridge.
    """

    def discover_host(self):
        devices = []
        event = threading.Event()
        def on_device_found(x):
            devices.append(x)
            event.set()

        zeroconf = Zeroconf()
        listener = MDNSListener(on_device_found)
        browser = ServiceBrowser(zeroconf, "_hue._tcp.local.", listener)

        event.wait(timeout=5)

        zeroconf.close()

        if not devices:
            raise DiscoveryFailed

        return socket.inet_ntoa(devices[0].addresses[0])


class DefaultDiscovery(object):
    """
    Discovery methods that tries all other discovery methods sequentially.
    """
    METHODS = [MDNSDiscovery, StaticHostDiscovery, NUPNPDiscovery]

    def discover(self):
        """ Tries all the discovery methods in self.METHODS. """
        for cls in self.METHODS:
            method = cls()
            try:
                return method.discover()
            except DiscoveryFailed:
                pass

        raise DiscoveryFailed
