
from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import forms, util
import sys

if sys.version_info.major < 3:
    text_type = unicode
    binary_type = str
else:
    text_type = str
    binary_type = bytes


class HStoreDictionary(dict):
    """
    A dictionary subclass which implements hstore support.
    """
    def __init__(self, value=None, field=None, instance=None, **params):
        super(HStoreDictionary, self).__init__(value, **params)
        self.field = field
        self.instance = instance

    def remove(self, keys):
        """
        Removes the specified keys from this dictionary.
        """
        queryset = self.instance._base_manager.get_query_set()
        queryset.filter(pk=self.instance.pk).hremove(self.field.name, keys)


class HStoreDescriptor(models.fields.subclassing.Creator):
    def __set__(self, obj, value):
        value = self.field.to_python(value)

        if not isinstance(value, HStoreDictionary):
            value = self.field._attribute_class(value, self.field, obj)

        obj.__dict__[self.field.name] = value


class HStoreField(models.Field):
    _attribute_class = HStoreDictionary
    _descriptor_class = HStoreDescriptor

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', lambda: {})
        super(HStoreField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(HStoreField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self._descriptor_class(self))

    def db_type(self, connection=None):
        return 'hstore'

    def get_prep_value(self, data):
        if not isinstance(data, (dict, HStoreDictionary)):
            return data

        for key in data:
            if not isinstance(data[key], (text_type, binary_type)):
                data[key] = text_type(data[key])

        return data

class DictionaryField(HStoreField):
    description = _("A python dictionary in a postgresql hstore field.")

    def formfield(self, **params):
        params['form_class'] = forms.DictionaryField
        return super(DictionaryField, self).formfield(**params)

    def get_prep_lookup(self, lookup, value):
        return value

    def to_python(self, value):
        return value or {}

    def _value_to_python(self, value):
        return value


class ReferencesField(HStoreField):
    description = _("A python dictionary of references to model instances in an hstore field.")

    def formfield(self, **params):
        params['form_class'] = forms.ReferencesField
        return super(ReferencesField, self).formfield(**params)

    def get_prep_lookup(self, lookup, value):
        return util.serialize_references(value) if isinstance(value, dict) else value

    def get_prep_value(self, value):
        return util.serialize_references(value) if value else {}

    def to_python(self, value):
        return util.unserialize_references(value) if value else {}

    def _value_to_python(self, value):
        return util.acquire_reference(value) if value else None

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(rules=[], patterns=['djorm_hstore.fields\.DictionaryField'])
except ImportError:
    pass
