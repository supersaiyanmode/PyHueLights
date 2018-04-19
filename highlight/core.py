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
    def __init__(self, parent=None, attr_in_parent=None):
        self.parent = parent
        self.attr_in_parent = attr_in_parent
        self.dirty_flag = {}

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


class Bridge(HueResource):
    """ Represents a Philips Hue bridge."""

    def __init__(self, host):
        self.host = host
