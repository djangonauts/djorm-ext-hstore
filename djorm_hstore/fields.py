# -*- coding: utf-8 -*-
import sys
import json

from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import forms, util

if sys.version_info[0] < 3:
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

    def __getstate__(self):
        """
        Returns pickable Python dict.
        """
        return dict(self)


class HStoreDescriptor(models.fields.subclassing.Creator):
    def __set__(self, obj, value):
        value = self.field.to_python(value)

        if isinstance(value, dict):
            value = self.field._attribute_class(value, self.field, obj)

        obj.__dict__[self.field.name] = value

    def __getstate__(self):
        """
        Returns pickable Python dict.
        """
        to_pickle = self.__dict__.copy()
        del to_pickle['default']
        return to_pickle


class HStoreField(models.Field):
    _attribute_class = HStoreDictionary
    _descriptor_class = HStoreDescriptor

    def __init__(self, *args, **kwargs):
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
            if data[key] is None:
                continue
            if not isinstance(data[key], (util.string_type, util.bytes_type)):
                data[key] = util.string_type(data[key])

        return data


class DictionaryField(HStoreField):
    description = _("A python dictionary in a postgresql hstore field.")

    def formfield(self, **params):
        params.setdefault("form_class", forms.DictionaryField)
        return super(DictionaryField, self).formfield(**params)

    def value_from_object(self, obj):
        """
        Return a sorted JSON string.
        """
        value = super(DictionaryField, self).value_from_object(obj)
        if value is not None:
            return json.dumps(value, sort_keys=True)

    def get_prep_lookup(self, lookup, value):
        return value

    def to_python(self, value):
        if value is None:
            return None

        if isinstance(value, util.string_type) and value:
            try:
                return json.loads(value)
            except ValueError:
                return {}

        return value or {}

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        prepped = self.get_prep_value(value)
        return json.dumps(prepped)

    def _value_to_python(self, value):
        return value


class ReferencesField(HStoreField):
    description = _("A python dictionary of references to model instances in an hstore field.")

    def formfield(self, **params):
        params.setdefault("form_class", forms.ReferencesField)
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
    add_introspection_rules(rules=[], patterns=['djorm_hstore.fields\.ReferencesField'])
except ImportError:
    pass
