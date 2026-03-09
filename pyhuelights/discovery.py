"""
This module contains all the discovery method used to discover the Philips
Hue bridge on the current network.
"""

import socket
import asyncio

import httpx
from zeroconf import ServiceBrowser, ServiceListener
from zeroconf.asyncio import AsyncZeroconf

from .exceptions import DiscoveryFailed


class MDNSListener(ServiceListener):

    def __init__(self, callback):
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

    async def validate(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://{}/description.xml".format(
                    self.host),
                                        timeout=5.0)
                if resp.status_code != 200:
                    return False
                return "Philips" in resp.text
        except (httpx.RequestError, httpx.TimeoutException):
            return False


class BaseDiscovery(object):

    async def discover(self):
        host = await self.discover_host()
        connection_info = await self.validate_host(host)
        return self.discovery_finished(connection_info)

    async def validate_host(self, host):
        connection_info = UnauthenticatedHueRawConnectionInfo(host)

        if not await connection_info.validate():
            raise DiscoveryFailed

        return connection_info

    async def discover_host(self):
        raise NotImplementedError

    def discovery_finished(self, connection_info):
        return connection_info


class NUPNPDiscovery(BaseDiscovery):
    """
    Uses NUPNP_URL below to discover the bridge as long as it is on the same
    network.
    """

    NUPNP_URL = "https://discovery.meethue.com"

    async def discover_host(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.NUPNP_URL, timeout=10.0)
                obj = resp.json()
        except (httpx.RequestError, ValueError):
            raise DiscoveryFailed

        if not isinstance(obj, list) or len(obj) == 0:
            raise DiscoveryFailed
        try:
            return obj[0]['internalipaddress']
        except KeyError:
            raise DiscoveryFailed


class StaticHostDiscovery(BaseDiscovery):
    """
    Assumes the hostname 'philips-hue' and tries to connect.
    """

    async def discover_host(self):
        return 'philips-hue'


class MDNSDiscovery(BaseDiscovery):
    """
    MDNS based discovery of the Hue bridge.
    """

    async def discover_host(self):
        devices = []
        event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def on_device_found(x):
            if x:
                devices.append(x)
                loop.call_soon_threadsafe(event.set)

        aio_zc = AsyncZeroconf()
        listener = MDNSListener(on_device_found)
        browser = ServiceBrowser(aio_zc.zeroconf, "_hue._tcp.local.", listener)

        try:
            await asyncio.wait_for(event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pass
        finally:
            browser.cancel()
            await aio_zc.async_close()

        if not devices:
            raise DiscoveryFailed

        return socket.inet_ntoa(devices[0].addresses[0])


class DefaultDiscovery(object):
    """
    Discovery methods that tries all other discovery methods sequentially.
    """
    METHODS = [MDNSDiscovery, StaticHostDiscovery, NUPNPDiscovery]

    async def discover(self):
        for cls in self.METHODS:
            method = cls()
            try:
                return await method.discover()
            except DiscoveryFailed:
                pass

        raise DiscoveryFailed
