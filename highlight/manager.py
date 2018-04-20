import requests

from .core import update_from_object
from .core import HueResource, Light
from .exceptions import RequestFailed


def dict_parser(cls):
    def parser(response):
        obj = {}
        for key, value in response.items():
            result = cls()
            update_from_object(result, key, value)
            obj[key] = result
        return obj

    return parser


def construct_body(obj):
    if obj is None:
        return None

    result = {}
    for field, value in obj.dirty_flag.items():
        if not value:
            continue
        field_value = getattr(obj, field)
        if isinstance(field_value, HueResource):
            transformed_value = construct_body(field_value)
        else:
            transformed_value = field_value
        result[obj.property_to_json_key_map[field]] = transformed_value
    return result


class BaseResourceManager(object):
    APIS = {}

    def __init__(self, connection_info):
        self.connection_info = connection_info

    def parse_response(self, obj, **kwargs):
        parser = kwargs.pop('parser')
        return parser(obj)

    def request(self, **kwargs):
        return self.parse_response(self.make_request(**kwargs), **kwargs)

    def make_request(self, **kwargs):
        expected_status = kwargs.pop('expected_status', [200])
        relative_url = kwargs.pop('relative_url')
        method = kwargs.pop('method')
        body = kwargs.pop('body', None)

        url = "http://{}/api/{}{}".format(self.connection_info.host,
                                          self.connection_info.username,
                                          relative_url)
        response = getattr(requests, method)(url, json=body)

        if response.status_code not in expected_status:
            raise RequestFailed(response.status_code, response.text)
        return response.json()

    def make_resource_update_request(self, obj, method='put', **kwargs):
        return self.make_request(method=method, relative_url=obj.relative_url(),
                                 body=construct_body(obj), **kwargs)

    def __getattr__(self, key):
        if key in self.APIS:
            return lambda **kwargs: self.request(**self.APIS[key])
        raise AttributeError


class LightsManager(BaseResourceManager):
    APIS = {
        'get_all_lights': {
            'relative_url': '/lights',
            'method': 'get',
            'parser': dict_parser(Light)
        }
    }

    def run_effect(self, light, effect):
        """
        Runs the change represented by effect on the given light instance.
        """
        light.clear_dirty()
        for state in effect.update_state(light):
            self.make_resource_update_request(state)
