import json
import requests
from requests_sse import EventSource

from .core import HueResource, Light, Group, update_from_object
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

    def make_resource_get_request(self, obj, relative_url=None):
        return self.make_request(method='get',
                                 relative_url=(relative_url
                                               or obj.relative_url()))

    def make_resource_update_request(self, obj, method='put', **kwargs):
        return self.make_request(method=method,
                                 relative_url=obj.relative_url(),
                                 body=construct_body(obj),
                                 **kwargs)


class LightsManager(BaseResourceManager):

    def get_all_lights(self):
        """ Retrieves all lights from the bridge, and returns a dict."""
        obj = self.make_request(relative_url="/lights", method="get")
        return self.parse_response(obj, parser=dict_parser(Light))

    def get_resource(self, resource=None, resource_id=None, typ=None):
        """ Retrieves the latest state of the provided resource. """
        if resource:
            res = self.make_resource_get_request(resource)
            resp = resource.__class__()
            update_from_object(resp, resource.id, res)
            return resp
        elif resource_id is not None and typ is not None:
            resource = typ()
            res = self.make_resource_get_request(
                resource, typ.make_relative_url(resource_id))
            update_from_object(resource, resource_id, res)
            return resource

        raise ValueError("Expected one of resource or <resource_id, typ>")

    def get_all_groups(self):
        """ Retrieves all groups on the bridge."""
        obj = self.make_request(relative_url='/groups', method='get')
        return self.parse_response(obj, parser=dict_parser(Group))

    def run_effect(self, light, effect):
        """
        Runs the change represented by effect on the given light instance.
        """
        if isinstance(light, Light):
            light.reset()
        else:
            for l in light:
                l.reset()

        for state in effect.update_state(light):
            res = self.make_resource_update_request(state)

    def iter_events(self):
        url = 'https://' + self.connection_info.host + '/eventstream/clip/v2'
        headers = {'hue-application-key': self.connection_info.username}
        with EventSource(url, headers=headers, verify=False) as events:
            for event in events:
                for change in json.loads(event.data):
                    for data in change["data"]:
                        light_id = data.get("id_v1")
                        if not light_id or not light_id.startswith("/lights"):
                            continue

                        yield self.get_resource(resource_id=light_id.replace(
                            "/lights/", ""),
                                                typ=Light)
