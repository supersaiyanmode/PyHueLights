""" Contains HueApp, Bridge, Light classes."""

import math
from dataclasses import dataclass, field
from typing import Type, Callable
from collections.abc import Collection


EMPTY = object()


def contains(params):
    def evaluate(arg):
        return arg in params

    return evaluate


def validate_xy(value):
    return isinstance(value, Collection) and len(value) == 2


def validate_temp(value):
    return 153 <= value <= 500


def rgb_to_xy(r, g, b):
    # This is based on original code from http://stackoverflow.com/a/22649803
    def enhance_color(normalized):
        if normalized > 0.04045:
            return math.pow((normalized + 0.055) / (1.0 + 0.055), 2.4)
        else:
            return normalized / 12.92

    r = enhance_color(r / 255.0)
    g = enhance_color(g / 255.0)
    b = enhance_color(b / 255.0)

    x = r * 0.649926 + g * 0.103455 + b * 0.197109
    y = r * 0.234327 + g * 0.743075 + b * 0.022598
    z = r * 0.000000 + g * 0.053077 + b * 1.035763

    if x + y + z == 0:
        return 0, 0
    else:
        return x / (x + y + z), y / (x + y + z)


class Color:
    def __init__(self, temp=None, xy=None):
        if not xy and not temp:
            raise ValueError("One of temp or xy must be provided.")

        if xy and not validate_xy(xy):
            raise ValueError("Bad xy value.")

        if temp and not validate_temp(temp):
            raise ValueError("Temperature should be between 2000 and 6500")

        if xy:
            self.color_mode = 'xy'
        elif temp:
            self.color_mode = 'ct'

        self.xy = xy
        self.temperature = temp

    @staticmethod
    def from_rgb(r, g, b):
        return Color(xy=rgb_to_xy(r, g, b))

    @staticmethod
    def from_temperature(temp):
        return Color(temp=int(1000000.0 / temp))


class HueResource(object):
    def __init__(self, parent=None, attr_in_parent=None):
        self.parent = parent
        self.attr_in_parent = attr_in_parent
        self.dirty_flag = {}  # Keyed by python property names.
        self.data = {}
        self.property_to_json_key_map = {}
        for field in self.FIELDS:
            field.init_object(self)
            self.property_to_json_key_map[field.prop_name()] = field.json_name()

    def relative_url(self):
        """
        Returns relative_url to construct the HTTP resource URL.
        """
        return ""

    def commit(self, prop_name=None):
        if prop_name and prop_name in self.dirty_flag:
            value = getattr(self, prop_name)
            if isinstance(value, HueResource):
                value.commit()
            else:
                self.data[prop_name + "_orig"] = value
            self.dirty_flag[prop_name] = False
        else:
            for key in self.dirty_flag:
                self.commit(prop_name=key)

    def reset(self):
        for field in self.FIELDS:
            if field.can_be_dirty() and field.prop_name() in self.dirty_flag:
                field.reset(self)


@dataclass
class Field(object):
    obj_prop_name: str
    parse_json_name: str = None
    writable: str = True
    cls: Type[HueResource] = None
    is_key: bool = False
    parse: bool = True
    optional: bool = False
    validator: Callable[..., str] = None

    def prop_name(self):
        return self.obj_prop_name

    def json_name(self):
        return self.parse_json_name or self.prop_name()

    def can_be_dirty(self):
        if self.is_key:
            return False
        return self.writable or self.cls is not None

    def init_object(self, obj):
        if (self.cls or self.writable) and not self.is_key:
            obj.dirty_flag[self.prop_name()] = False

        if self.optional or not self.parse:
            obj.data[self.prop_name()] = EMPTY
            obj.data[self.prop_name() + "_orig"] = EMPTY

        field = self

        def getter_func(self):
            return self.data[field.prop_name()]

        def setter_func(self, val):
            if (field.optional and
                self.data.get(field.prop_name(), EMPTY) is EMPTY):
                raise ValueError("Unsupported operation on this field.")

            if field.validator and not field.validator(val):
                raise ValueError(val)

            self.data[field.prop_name()] = val

            # Walk up the hierarchy and set the dirty flags.
            current_obj = self
            current_attr = field.prop_name()
            while current_obj is not None:
                current_obj.dirty_flag[current_attr] = True
                current_attr = current_obj.attr_in_parent
                current_obj = current_obj.parent

        kwargs = {"fget": getter_func}
        if self.writable and not self.cls and not self.is_key:
            kwargs["fset"] = setter_func
        setattr(obj.__class__, self.prop_name(), property(**kwargs))

    def update(self, obj, key, json):
        if not self.parse:
            return

        if self.is_key:
            obj.data[self.prop_name()] = key
            return

        if self.cls:
            if (self.json_name() not in json or
                not isinstance(json[self.json_name()], dict)):
                raise ValueError(f"Expected object for: {self}, in {json} at " +
                                 self.json_name())
            value = self.cls(parent=obj, attr_in_parent=self.prop_name())
            update_from_object(value, None, json[self.json_name()])
            obj.dirty_flag[self.prop_name()] = False
            obj.data[self.prop_name()] = value
        elif self.json_name() in json:
            obj.data[self.prop_name()] = json[self.json_name()]
            obj.data[self.prop_name() + "_orig"] = json[self.json_name()]
            obj.dirty_flag[self.prop_name()] = False
        elif self.optional and self.json_name() not in json:
            obj.data[self.prop_name()] = EMPTY
            # init_object takes care of self.prop_name() + "_orig".
        else:
            raise ValueError("Field absent in response: " + self.json_name())

    def reset(self, obj):
        if self.cls:
            getattr(obj, self.prop_name()).reset()
        else:
            obj.data[self.prop_name()] = obj.data[self.prop_name() + "_orig"]
        obj.dirty_flag[self.prop_name()] = False



class HueApp(HueResource):
    """ Represents Hue App. """

    FIELDS = []

    def __init__(self, app_name, client_name):
        super(HueApp, self).__init__()
        self.app_name = app_name
        self.client_name = client_name


class LightState(HueResource):
    """ Represents the state of the light (colors, brightness etc). """

    FIELDS = [
        Field(obj_prop_name="on"),
        Field(obj_prop_name="reachable", writable=False),
        Field(obj_prop_name="color_mode", parse_json_name="colormode",
              validator=contains({"ct", "hs", "xy"})),
        Field(obj_prop_name="saturation", parse_json_name="sat",
              validator=contains(range(1, 255)), optional=True),
        Field(obj_prop_name="brightness", parse_json_name="bri",
              validator=contains(range(1, 255)), optional=True),
        Field(obj_prop_name="hue", parse_json_name="hue",
              validator=contains(range(1, 65536)), optional=True),
        Field(obj_prop_name="temperature", parse_json_name="ct",
              validator=contains(range(153, 501)), optional=True),
        Field(obj_prop_name="xy", parse_json_name="xy",optional=True,
              validator=validate_xy),
        Field(obj_prop_name="effect", validator=contains({"colorloop", "none"}),
              optional=True),
        Field(obj_prop_name="transition_time", parse_json_name="transitiontime",
              parse=False),
    ]

    def relative_url(self):
        return self.parent.relative_url() + "/state"

    def set_color(self, color: Color):
        if not isinstance(color, Color):
            raise ValueError("Expected a Color instance.")

        if color.color_mode == 'xy':
            self.xy = color.xy
        elif color.color_mode == 'ct':
            self.temperature = color.temperature
        else:
            raise ValueError("Unsupported color mode.")

        self.color_mode = color.color_mode


class Light(HueResource):
    FIELDS = [
        Field(obj_prop_name="id", is_key=True),
        Field(obj_prop_name="unique_id", parse_json_name="uniqueid",
              writable=False),
        Field(obj_prop_name="type", writable=False),
        Field(obj_prop_name="model_id", parse_json_name="modelid",
              writable=False),
        Field(obj_prop_name="software_version", parse_json_name="swversion",
              writable=False),
        Field(obj_prop_name="name"),
        Field(obj_prop_name="state", cls=LightState),
    ]

    def relative_url(self):
        return "/lights/" + self.id


class GroupState(HueResource):
    """ Represents the state of the lights in group. """

    FIELDS = [
        Field(obj_prop_name="on"),
        Field(obj_prop_name="reachable", writable=False, optional=True),
        Field(obj_prop_name="color_mode", parse_json_name="colormode"),
        Field(obj_prop_name="effect", validator=contains({"colorloop", "none"}),
              optional=True),
        Field(obj_prop_name="transition_time", parse_json_name="transitiontime",
              parse=False),
    ]

    def relative_url(self):
        return self.parent.relative_url() + "/action"


class Group(HueResource):
    FIELDS = [
        Field(obj_prop_name="id", is_key=True),
        Field(obj_prop_name="lights", optional=True),
        Field(obj_prop_name="name"),
        Field(obj_prop_name="type", writable=False),
        Field(obj_prop_name="group_class", parse_json_name="class",
              optional=True),
        Field(obj_prop_name="state", parse_json_name="action", cls=GroupState),
        Field(obj_prop_name="model_id", parse_json_name="modelid",
              writable=False, optional=True),
    ]

    def relative_url(self):
        return "/groups/" + self.id


def update_from_object(resource, key, json):
    for field in resource.FIELDS:
        field.update(resource, key, json)

