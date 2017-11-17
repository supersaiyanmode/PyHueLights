""" Contains HueApp, Bridge, Light classes."""


import requests

from .exceptions import RequestFailed


def make_property(obj, attr_name, obj_prop_name, field_info, dirty):
    def getter_func(self):
        return getattr(self, attr_name)

    def setter_func(self, val):
        setattr(self, attr_name, val)
        dirty[obj_prop_name] = True


    if field_info.get("readonly", False):
        prop = property(fget=getter_func)
    else:
        prop = property(fget=getter_func, fset=setter_func)
        dirty[obj_prop_name] = False

    setattr(obj.__class__, obj_prop_name, prop)


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
        self.dirty_flag = {}

    def get(self, relative_url=None):
        return self.make_request('get')

    def put(self, params, relative_url=None):
        return self.make_request('put')

    def delete(self, relative_url=None):
        return self.make_request('delete', relative_url=relative_url)

    def make_request(self, method, *args, **kwargs):
        expected_status = kwargs.pop('expected_status', [])
        relative_url = kwargs.pop('relative_url', self.relative_url)

        url = self.format_url(self.connection_info, relative_url)
        response = getattr(requests, method)(url, *args, **kwargs)
        if response.status_code not in expected_status:
            raise RequestFailed(response.status_code, response.text)
        return response.json()

    def format_url(self, connection_info, relative_url=None):
        """
        Use connection_info and relative_url to construct the HTTP resource
        URL.
        """
        return "http://{}/api/{}/{}".format(connection_info.host,
                                            connection_info.username,
                                            self.relative_url)

    def update_from_object(self, obj):
        for field_info in self.FIELDS:
            json_item_name = field_info.get('field', field_info["name"])
            obj_prop_name = field_info["name"]
            obj_attr_name = "field_" + obj_prop_name

            if json_item_name not in obj:
                raise ValueError("No field in object: " + json_item_name)

            setattr(self, obj_attr_name, obj[json_item_name])
            make_property(self, obj_attr_name, obj_prop_name, field_info,
                          self.dirty_flag)


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
