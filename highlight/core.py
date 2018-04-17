""" Contains HueApp, Bridge, Light classes."""


import requests

from .exceptions import RequestFailed


def make_property(obj, attr_name, obj_prop_name, field_info, dirty):
    def getter_func(self):
        return getattr(self, attr_name)

    def setter_func(self, val):
        setattr(self, attr_name, val)
        dirty[obj_prop_name] = True

    # No setters for a sub-resource or a readonly resource.
    if field_info.get("readonly", False) or field_info.get('cls'):
        prop = property(fget=getter_func)
    else:
        prop = property(fget=getter_func, fset=setter_func)
        dirty[obj_prop_name] = False

    setattr(obj.__class__, obj_prop_name, prop)


def update_from_object(result, obj, fields, dirty_flag, sub_res_args=()):
    for field_info in fields:
        sub_resource = field_info.get('cls')
        json_item_name = field_info.get('field', field_info["name"])
        obj_prop_name = field_info["name"]
        obj_attr_name = "field_" + obj_prop_name

        if json_item_name not in obj:
            raise ValueError("No field in object: " + json_item_name)

        if sub_resource:
            value = sub_resource(*sub_res_args)
        else:
            value = obj[json_item_name]

        setattr(result, obj_attr_name, value)
        make_property(result, obj_attr_name, obj_prop_name, field_info,
                      dirty_flag)


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


class BaseRequest(object):
    def parse_response(self, method, obj):
        return self.RESPONSE_PARSERS[method](obj)

    def request(self, method, **kwargs):
        return self.parse_response(self.make_request(method, **kwargs))


class Get(BaseRequest):
    def get(self, **kwargs):
        return self.request('get', **kwargs)


class Post(object):
    def post(self, **kwargs):
        return self.request('post', **kwargs)


class Put(object):
    def put(self, obj, **kwargs):
        return self.request('put', **kwargs)


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
