import requests

from .core import Light
from .exceptions import RequestFailed


def make_property(obj, attr_name, obj_prop_name, field_info):
    def getter_func(self):
        return getattr(self, attr_name)

    def setter_func(self, val):
        setattr(self, attr_name, val)
        obj.set_dirty(obj_prop_name)

    # No setters for a sub-resource or a readonly resource.
    if field_info.get("readonly", False) or field_info.get('cls'):
        prop = property(fget=getter_func)
    else:
        prop = property(fget=getter_func, fset=setter_func)
        obj.dirty_flag[obj_prop_name] = False

    setattr(obj.__class__, obj_prop_name, prop)


def update_from_object(result, key, obj):
    if not hasattr(result, 'FIELDS'):
        raise ValueError("Invalid target. Doesn't have FIELDS attribute.")

    for field_info in result.FIELDS:
        sub_resource = field_info.get('cls')
        json_item_name = field_info.get('field', field_info["name"])
        obj_prop_name = field_info["name"]
        obj_attr_name = "field_" + obj_prop_name

        if json_item_name != "$KEY" and json_item_name not in obj:
            raise ValueError("No field in object: " + json_item_name)

        if sub_resource:
            value = sub_resource(parent=result, attr_in_parent=obj_prop_name)
            update_from_object(value, None, obj[json_item_name])
        elif json_item_name == "$KEY":
            field_info["readonly"] = True
            value = key
        else:
            value = obj[json_item_name]

        setattr(result, obj_attr_name, value)
        make_property(result, obj_attr_name, obj_prop_name, field_info)


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
    return None


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
        response = getattr(requests, method)(url, json=construct_body(body))
        if response.status_code not in expected_status:
            raise RequestFailed(response.status_code, response.text)
        return response.json()

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
