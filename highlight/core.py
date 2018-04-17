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

        return "Philips" in resp.text


class HueResource(object):
    def __init__(self, connection_info, parent=None):
        self.connection_info = connection_info
        self.parent = parent
        self.dirty_flag = {}

    def make_request(self, method, **kwargs):
        expected_status = kwargs.pop('expected_status', [])
        relative_url = kwargs.pop('relative_url', self.relative_url)

        url = self.format_url(self.connection_info, relative_url)
        response = getattr(requests, method)(url, **kwargs)
        if expected_status and response.status_code not in expected_status:
            raise RequestFailed(response.status_code, response.text)
        return response.json()

    def format_url(self):
        """
        Use connection_info and relative_url to construct the HTTP resource
        URL.
        """
        return "http://{}/api/{}".format(
                self.connection_info.host, self.connection_info.username)

    def update_from_object(self, obj):
        args = (self.connection_info, self)
        update_from_object(self, obj, self.FIELDS, self.dirty_flag, args)


class HueApp(HueResource):
    """ Represents Hue App. """
    def __init__(self, app_name, client_name):
        self.app_name = app_name
        self.client_name = client_name

    def format_url(self):
        return super(HueApp, self).format_url().rstrip('/')


class LightState(HueResource):
    """ Represents the state of the light (colors, brightness etc). """

    FIELDS = [
        {"name": "on"},
        {"name": "reachable", "readonly": True},
        {"name": "color_mode", "field": "colormode", "readonly": True},
    ]

    def format_url(self):
        return self.parent.format_url() + "/state"


class Light(HueResource):
    FIELDS = [
        {"name": "type", "readonly": True},
        {"name": "model_id", "field": "modelid", "readonly": True},
        {"name": "software_version", "field": "swversion", "readonly": True},
        {"name": "name"},
        {"name": "state", "cls": LightState}
    ]

    def format_url(self):
        return super(Light, self).format_url() + "/lights"


class Bridge(HueResource):
    """ Represents a Philips Hue bridge."""

    def __init__(self, host):
        self.host = host
