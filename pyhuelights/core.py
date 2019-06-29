""" Contains HueApp, Bridge, Light classes."""


import requests


def validate_setter_values(field_info, val):
    allowed_values = field_info.get("values")
    if allowed_values and val not in allowed_values:
        raise ValueError("Not a valid value.")


def make_property(obj, attr_name, obj_prop_name, field_info):
    def getter_func(self):
        return getattr(self, attr_name)

    def setter_func(self, val):
        validate_setter_values(field_info, val)
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

    for field_info in result.FIELDS:
        sub_resource = field_info.get('cls')
        json_item_name = field_info.get('field', field_info["name"])
        obj_prop_name = field_info["name"]
        obj_attr_name = "field_" + obj_prop_name

        if json_item_name != "$KEY" and json_item_name not in obj and \
                not field_info.get("optional"):
            raise ValueError("No field in object: " + json_item_name)

        if sub_resource:
            value = sub_resource(parent=result, attr_in_parent=obj_prop_name)
            update_from_object(value, None, obj[json_item_name])
        elif json_item_name == "$KEY":
            field_info["readonly"] = True
            value = key
        elif field_info.get("optional"):
            value = obj.get(json_item_name)
        else:
            value = obj[json_item_name]

        setattr(result, obj_prop_name + "_orig", value)
        setattr(result, obj_attr_name, value)
        make_property(result, obj_attr_name, obj_prop_name, field_info)

        result.property_to_json_key_map[obj_prop_name] = json_item_name


def init_object(obj):
    if not hasattr(obj, 'REQUEST_FIELDS'):
        return

    def make_property(field_info, prop_name, attr_name):
        def getter(self):
            return getattr(self, attr_name, None)

        def setter(self, val):
            validate_setter_values(field_info, val)
            setattr(self, attr_name, val)
            self.set_dirty(prop_name)

        return getter, setter

    for field_info in obj.REQUEST_FIELDS:
        prop_name = field_info["name"]
        json_item_name = field_info.get("field", prop_name)

        getter, setter = make_property(field_info, prop_name,
                                       "field_" + prop_name)
        prop = property(fget=getter, fset=setter)
        setattr(obj.__class__, prop_name, prop)

        setattr(obj, prop_name + "_orig", None)

        obj.property_to_json_key_map[prop_name] = json_item_name


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
    def __init__(self, parent=None, attr_in_parent=None):
        self.parent = parent
        self.attr_in_parent = attr_in_parent
        self.dirty_flag = {}
        self.property_to_json_key_map = {}
        init_object(self)

    def relative_url(self):
        """
        Returns relative_url to construct the HTTP resource URL.
        """
        return ""

    def set_dirty(self, field):
        self.dirty_flag[field] = True
        if self.parent:
            self.parent.set_dirty(self.attr_in_parent)

    def clear_dirty(self, field=None):
        if field and field in self.dirty_flag:
            value = getattr(self, field)
            if isinstance(value, HueResource):
                value.clear_dirty(field=field)
            else:
                setattr(self, "field_" + field, getattr(self, field + "_orig"))
            self.dirty_flag[field] = False
        else:
            for key in self.dirty_flag:
                self.clear_dirty(field=key)

    def update_state(self, field=None):
        if field and field in self.dirty_flag:
            value = getattr(self, field)
            if isinstance(value, HueResource):
                value.update_state()
            else:
                setattr(self, field + "_orig", value)
            self.dirty_flag[field] = False
        else:
            for key in self.dirty_flag:
                self.update_state(field=key)


class HueApp(HueResource):
    """ Represents Hue App. """
    def __init__(self, app_name, client_name):
        super(HueApp, self).__init__()
        self.app_name = app_name
        self.client_name = client_name


class LightState(HueResource):
    """ Represents the state of the light (colors, brightness etc). """

    FIELDS = [
        {"name": "on"},
        {"name": "reachable", "readonly": True},
        {"name": "color_mode", "field": "colormode", "readonly": True},
        {"name": "effect", "values": ["colorloop", "none"]},
    ]

    REQUEST_FIELDS = [
        {"name": "transition_time", "field": "transitiontime"},
    ]

    def relative_url(self):
        return self.parent.relative_url() + "/state"


class Light(HueResource):
    FIELDS = [
        {"name": "id", "field": "$KEY"},
        {"name": "type", "readonly": True},
        {"name": "model_id", "field": "modelid", "readonly": True},
        {"name": "software_version", "field": "swversion", "readonly": True},
        {"name": "name"},
        {"name": "state", "cls": LightState}
    ]

    def relative_url(self):
        return "/lights/" + self.id


class GroupState(HueResource):
    """ Represents the state of the lights in group. """

    FIELDS = [
        {"name": "on"},
        {"name": "reachable", "readonly": True, "optional": True},
        {"name": "color_mode", "field": "colormode", "readonly": True},
        {"name": "effect", "values": ["colorloop", "none"]},
    ]

    REQUEST_FIELDS = [
        {"name": "transition_time", "field": "transitiontime"},
    ]

    def relative_url(self):
        return self.parent.relative_url() + "/action"


class Group(HueResource):
    FIELDS = [
        {"name": "id", "field": "$KEY"},
        {"name": "lights", "optional": True},
        {"name": "name"},
        {"name": "type"},
        {"name": "group_class", "field": "class", "optional": True},
        {"name": "state", "field": "action", "cls": GroupState},
        {"name": "model_id", "field": "modelid", "readonly": True,
         "optional": True},
    ]

    def relative_url(self):
        return "/groups/" + self.id
