""" Contains network management logic. """

import json
from typing import Any, Callable, Dict, Type, AsyncGenerator
import httpx
from httpx_sse import aconnect_sse

from .model import HueResource, update_from_object
from .exceptions import RequestFailed


def dict_parser(
    cls: Type[HueResource]
) -> Callable[[Dict[str, Any]], Dict[str, HueResource]]:

    def parser(response: Dict[str, Any]) -> Dict[str, HueResource]:
        obj = {}
        for key, value in response.items():
            result = cls()
            update_from_object(result, key, value)
            obj[key] = result
        return obj

    return parser


def construct_body(obj: HueResource | None) -> Dict[str, Any] | None:
    if obj is None:
        return None

    result = {}
    for field in obj.FIELDS:
        if obj.dirty_flag.get(field.prop_name(), False):
            field_value = getattr(obj, field.prop_name())
            if isinstance(field_value, HueResource):
                transformed_value = construct_body(field_value)
            else:
                transformed_value = field.to_json_converter(field_value)

            result[obj.property_to_json_key_map[
                field.prop_name()]] = transformed_value

    return result


class BaseResourceManager(object):
    APIS = {}

    def __init__(self,
                 connection_info: Any,
                 client: httpx.AsyncClient | None = None):
        self.connection_info = connection_info
        self._client = client

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    def parse_response(self, obj: Any, **kwargs: Any) -> Any:
        parser = kwargs.pop('parser')
        return parser(obj)

    async def make_request(self, **kwargs: Any) -> Any:
        expected_status = kwargs.pop('expected_status', [200])
        relative_url = kwargs.pop('relative_url')
        method = kwargs.pop('method')
        body = kwargs.pop('body', None)

        url = "http://{}/api/{}{}".format(self.connection_info.host,
                                          self.connection_info.username,
                                          relative_url)
        client = await self.get_client()
        response = await client.request(method, url, json=body)

        if response.status_code not in expected_status:
            raise RequestFailed(response.status_code, response.text)
        return response.json()

    async def make_resource_get_request(self,
                                        obj: HueResource,
                                        relative_url: str | None = None
                                        ) -> Any:
        return await self.make_request(method='get',
                                       relative_url=(relative_url
                                                     or obj.relative_url()))

    async def make_resource_update_request(self,
                                           obj: HueResource,
                                           method: str = 'put',
                                           **kwargs: Any) -> Any:
        return await self.make_request(method=method,
                                       relative_url=obj.relative_url(),
                                       body=construct_body(obj),
                                       **kwargs)

    async def get_resource(self,
                           resource: HueResource | None = None,
                           resource_id: str | None = None,
                           typ: Type[HueResource] | None = None) -> Any:
        """ Retrieves the latest state of the provided resource. """
        if resource:
            res = await self.make_resource_get_request(resource)
            resp = resource.__class__()
            update_from_object(resp, resource.id, res)
            return resp
        elif resource_id is not None and typ is not None:
            resource_obj = typ()
            res = await self.make_resource_get_request(
                resource_obj, typ.make_relative_url(resource_id))
            update_from_object(resource_obj, resource_id, res)
            return resource_obj

        raise ValueError("Expected one of resource or <resource_id, typ>")

    async def iter_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        url = 'https://' + self.connection_info.host + '/eventstream/clip/v2'
        headers = {'hue-application-key': self.connection_info.username}
        client = await self.get_client()
        async with aconnect_sse(client,
                                "GET",
                                url,
                                headers=headers,
                                verify=False) as event_source:
            async for event in event_source.aiter_sse():
                for change in json.loads(event.data):
                    yield change
