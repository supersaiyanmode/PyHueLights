import requests

from .core import HueResource, Light
from .exceptions import RequestFailed


def make_property(obj, attr_name, obj_prop_name, field_info, value):
    def getter_func(self):
        return getattr(self, attr_name)

    def setter_func(self, val):
        allowed_values = field_info.get("values")
        if allowed_values and val not in allowed_values:
            raise ValueError("Not a valid value.")
        setattr(self, attr_name, val)
        self.set_dirty(obj_prop_name)

    # No setters for a sub-resource or a readonly resource.
    if field_info.get("readonly", False):
        prop = property(fget=getter_func)
        setattr(obj.__class__, obj_prop_name, prop)
    elif field_info.get('cls'):
        prop = property(fget=getter_func)
        obj.dirty_flag[obj_prop_name] = False
        setattr(obj.__class__, obj_prop_name, prop)
    else:
        prop = property(fget=getter_func, fset=setter_func)
        obj.dirty_flag[obj_prop_name] = False
        setattr(obj.__class__, obj_prop_name, prop)


def update_from_object(result, key, obj):
    if not hasattr(result, 'FIELDS'):
        raise ValueError("Invalid target. Doesn't have FIELDS attribute.")

    prop_to_json_key_map = {}
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

        setattr(result, obj_prop_name + "_orig", value)
        setattr(result, obj_attr_name, value)
        make_property(result, obj_attr_name, obj_prop_name, field_info, value)

        prop_to_json_key_map[obj_prop_name] = json_item_name
    result.property_to_json_key_map = prop_to_json_key_map


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
