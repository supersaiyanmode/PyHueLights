from .exceptions import RequestFailed


def make_property(obj, attr_name, obj_prop_name, field_info):
    def getter_func(self):
        return getattr(self, attr_name)

    def setter_func(self, val):
        setattr(self, attr_name, val)
        obj.dirty_flag[obj_prop_name] = True

    # No setters for a sub-resource or a readonly resource.
    if field_info.get("readonly", False) or field_info.get('cls'):
        prop = property(fget=getter_func)
    else:
        prop = property(fget=getter_func, fset=setter_func)
        obj.dirty_flag[obj_prop_name] = False

    setattr(obj.__class__, obj_prop_name, prop)


def update_from_object(result, obj, fields):
    for field_info in fields:
        sub_resource = field_info.get('cls')
        json_item_name = field_info.get('field', field_info["name"])
        obj_prop_name = field_info["name"]
        obj_attr_name = "field_" + obj_prop_name

        if json_item_name not in obj:
            raise ValueError("No field in object: " + json_item_name)

        if sub_resource:
            value = sub_resource(parent=obj)
            update_from_object(value, obj[json_item_name], value.FIELDS)
        else:
            value = obj[json_item_name]

        setattr(result, obj_attr_name, value)
        make_property(result, obj_attr_name, obj_prop_name, field_info)
