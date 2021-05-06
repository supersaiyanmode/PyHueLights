""" Contains classes to help with register with Philips Hue Bridge. """

import time
from threading import Thread, Event

import requests

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
    def __init__(self, host, app_name, timeout, callback=None):
        self.url = "http://{}/api".format(host)
        self.app_name = app_name
        self.timeout = timeout
        self.thread = Thread(target=self.run)
        self.status = None
        self.username = None
        self.event = Event()

        self.callback = self.event.set if callback is None else callback

    def run(self):
        started = time.time()
        while time.time() - started < self.timeout:
            self.status = REGISTRATION_REQUESTED
            resp = requests.post(self.url, json={"devicetype": self.app_name})
            if resp.status_code != 200:
                self.status = REGISTRATION_FAILED
                break

            try:
                username = resp.json()[0]["success"]["username"]
                self.username = username
                self.status = REGISTRATION_SUCCEEDED
                break
            except (IOError, IndexError, KeyError):
                pass

            time.sleep(1)

        if self.status == REGISTRATION_REQUESTED:
            self.status = REGISTRATION_FAILED

        self.callback()

    def start(self):
        self.thread.start()

    def wait(self):
        self.event.wait()


def register(unauthenticated_connection, app, store, timeout=30.0):
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
    watcher.wait()

    if watcher.status == REGISTRATION_SUCCEEDED:
        store["username"] = watcher.username
        return AuthenticatedHueConnection(unauthenticated_connection.host,
                                          watcher.username)

    raise RegistrationFailed()
