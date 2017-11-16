""" Contains HueApp, Bridge, Light classes."""


import requests


class HueConnectionInfo(object):
    """ Represents the result of a Hue Bridge discovery. """
    def __init__(self, host, username=None):
        self.host = host
        self.username = username

    def validate(self):
        resp = requests.get("http://{}/description.xml".format(self.host))
        if resp.status_code != 200:
            return False

        if "Philips" not in resp.text:
            return False

        return True


class HueResource(object):
    def __init__(self, connection_info, relative_url):
        self.connection_info = connection_info
        self.relative_url = relative_url

    def get(self):
        url = self.format_url(self.connection_info)
        return requests.get(url).json()

    def put(self, params):
        url = self.format_url(self.connection_info)
        return requests.put(url, json=params).json()

    def delete(self):
        url = self.format_url(self.connection_info)
        return requests.delete(url).json()

    def format_url(self, connection_info):
        """
        Use connection_info and relative_url to construct the HTTP resource
        URL.
        """
        return "http://{}/api/{}/{}".format(connection_info.host,
                                            connection_info.username,
                                            self.relative_url)


class HueApp(HueResource):
    """ Represents Hue App. """
    def __init__(self, app_name, client_name):
        self.app_name = app_name
        self.client_name = client_name

    def format_url(self, connection_info):
        return "http://{}/api".format(connection_info.host)


class Bridge(object):
    """ Represents a Philips Hue bridge."""

    def __init__(self, host):
        self.host = host
