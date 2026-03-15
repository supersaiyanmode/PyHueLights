""" Contains classes to help with register with Philips Hue Bridge. """

import time
import asyncio
import inspect
from typing import Any, Callable

import httpx

from .exceptions import RegistrationFailed

REGISTRATION_REQUESTED = 1
REGISTRATION_SUCCEEDED = 2
REGISTRATION_FAILED = 3


class AuthenticatedHueConnection():
    """ Represents a Hue connection with valid username. """

    def __init__(self, host, username):
        self.host = host
        self.username = username


class RegistrationWatcher(object):

    def __init__(self,
                 host: str,
                 app_name: str,
                 timeout: float,
                 callback: Callable[[], Any] | None = None):
        self.url = "http://{}/api".format(host)
        self.app_name = app_name
        self.timeout = timeout
        self.status = None
        self.username = None
        self.event = asyncio.Event()
        self.callback = callback or self.event.set

    async def run(self):
        started = time.time()
        async with httpx.AsyncClient() as client:
            while time.time() - started < self.timeout:
                self.status = REGISTRATION_REQUESTED
                try:
                    resp = await client.post(
                        self.url, json={"devicetype": self.app_name})
                    if resp.status_code != 200:
                        self.status = REGISTRATION_FAILED
                        break

                    data = resp.json()
                    if isinstance(data, list) and "success" in data[0]:
                        self.username = data[0]["success"]["username"]
                        self.status = REGISTRATION_SUCCEEDED
                        break
                except (httpx.RequestError, IOError, IndexError, KeyError,
                        ValueError):
                    pass

                await asyncio.sleep(1)

        if self.status == REGISTRATION_REQUESTED:
            self.status = REGISTRATION_FAILED

        if inspect.iscoroutinefunction(self.callback):
            await self.callback()
        else:
            self.callback()

    def start(self):
        asyncio.create_task(self.run())

    async def wait(self):
        await self.event.wait()


async def register(unauthenticated_connection: Any,
                   app: Any,
                   store: dict,
                   timeout: float = 30.0) -> AuthenticatedHueConnection:
    """
    Looks into the store to check for previous registration. If absent, go ahead
    with new registration.
    """
    if "username" in store:
        return AuthenticatedHueConnection(unauthenticated_connection.host,
                                          store["username"])

    app_name = app.app_name + "#" + app.client_name
    watcher = RegistrationWatcher(unauthenticated_connection.host, app_name,
                                  timeout)
    watcher.start()
    await watcher.wait()

    if watcher.status == REGISTRATION_SUCCEEDED:
        store["username"] = watcher.username
        return AuthenticatedHueConnection(unauthenticated_connection.host,
                                          watcher.username)

    raise RegistrationFailed()
