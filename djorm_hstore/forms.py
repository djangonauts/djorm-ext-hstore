from django.forms import Field
from django.contrib.admin.widgets import AdminTextareaWidget
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from . import util
from .widgets import KeyValueWidget
import json


class JsonMixin(object):
    def to_python(self, value):
        try:
            if value is not None:
                return json.loads(value)
        except TypeError:
            raise ValidationError(_(u'String type is required.'))
        except ValueError:
            raise ValidationError(_(u'Enter a valid value.'))

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        try:
            # load/re-dump to sort by key for has_changed comparison
            value = json.dumps(json.loads(value), sort_keys=True)
        except (TypeError, ValueError):
            pass
        return value


class DictionaryFieldWidget(JsonMixin, AdminTextareaWidget):
    def render(self, name, value, attrs=None):
        if value:
            # a DictionaryField (model field) returns a string value via
            # value_from_object(), load and re-dump for indentation
            try:
                value = json.dumps(json.loads(value), sort_keys=True, indent=2)
            except ValueError:
                # Skip formatting if value is not valid JSON
                pass
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
        defaults = {
            'widget': KeyValueWidget,
            'initial': u'{}',
        }
        defaults.update(params)
        super(DictionaryField, self).__init__(**defaults)


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
