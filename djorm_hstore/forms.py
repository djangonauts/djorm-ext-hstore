from django.forms import Field
from django.contrib.admin.widgets import AdminTextareaWidget

from . import util
import json


class JsonMixin(object):
    def to_python(self, value):
        return json.loads(value)



class DictionaryFieldWidget(JsonMixin, AdminTextareaWidget):
    def render(self, name, value, attrs=None):
        if value:
            # a DictionaryField (model field) returns a string value via
            # value_from_object(), load and re-dump for indentation
            value = json.dumps(json.loads(value), sort_keys=True, indent=2)
        return super(JsonMixin, self).render(name, value, attrs)


class ReferencesFieldWidget(JsonMixin, AdminTextareaWidget):
    def render(self, name, value, attrs=None):
        value = util.serialize_references(value)
        return super(ReferencesFieldWidget, self).render(name, value, attrs)


class DictionaryField(JsonMixin, Field):
    """
    A dictionary form field.
    """
    def __init__(self, **params):
        params['widget'] = DictionaryFieldWidget
        params['initial'] = u'{}'
        super(DictionaryField, self).__init__(**params)


class ReferencesField(JsonMixin, Field):
    """
    A references form field.
    """
    def __init__(self, **params):
        params['widget'] = ReferencesFieldWidget
        super(ReferencesField, self).__init__(**params)

    def to_python(self, value):
        value = super(ReferencesField, self).to_python(value)
        return util.unserialize_references(value)
