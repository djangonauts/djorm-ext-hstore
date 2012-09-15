# -*- coding: utf-8 -*-

from django.db.models.sql.constants import SINGLE
from django.db.models.query_utils import QueryWrapper
from django.db.models.query import QuerySet
from django.db import models

from djorm_expressions.models import ExpressionQuerySetMixin, ExpressionManagerMixin

from .query_utils import select_query, update_query


class HStoreQuerysetMixin(object):
    @select_query
    def hkeys(self, query, attr):
        """
        Enumerates the keys in the specified hstore.
        """
        query.add_extra({'_': 'akeys("%s")' % attr}, None, None, None, None, None)
        result = query.get_compiler(self.db).execute_sql(SINGLE)
        return (result[0] if result else [])

    @select_query
    def hpeek(self, query, attr, key):
        """
        Peeks at a value of the specified key.
        """
        query.add_extra({'_': '%s -> %%s' % attr}, [key], None, None, None, None)
        result = query.get_compiler(self.db).execute_sql(SINGLE)
        if result and result[0]:
            field = self.model._meta.get_field_by_name(attr)[0]
            return field._value_to_python(result[0])

    @select_query
    def hslice(self, query, attr, keys):
        """
        Slices the specified key/value pairs.
        """
        query.add_extra({'_': 'slice("%s", %%s)' % attr}, [keys], None, None, None, None)
        result = query.get_compiler(self.db).execute_sql(SINGLE)
        if result and result[0]:
            field = self.model._meta.get_field_by_name(attr)[0]
            return dict((key, field._value_to_python(value)) for key, value in result[0].iteritems())
        return {}

    @update_query
    def hremove(self, query, attr, keys):
        """
        Removes the specified keys in the specified hstore.
        """
        value = QueryWrapper('delete("%s", %%s)' % attr, [keys])
        field, model, direct, m2m = self.model._meta.get_field_by_name(attr)
        query.add_update_fields([(field, None, value)])
        return query

    @update_query
    def hupdate(self, query, attr, updates):
        """
        Updates the specified hstore.
        """
        value = QueryWrapper('"%s" || %%s' % attr, [updates])
        field, model, direct, m2m = self.model._meta.get_field_by_name(attr)
        query.add_update_fields([(field, None, value)])
        return query


class HStoreQueryset(HStoreQuerysetMixin, ExpressionQuerySetMixin, QuerySet):
    pass


class HStoreManagerMixin(object):
    """
    Object manager which enables hstore features.
    """
    use_for_related_fields = True

    def hkeys(self, attr):
        return self.get_query_set().hkeys(attr)

    def hpeek(self, attr, key):
        return self.get_query_set().hpeek(attr, key)

    def hslice(self, attr, keys, **params):
        return self.get_query_set().hslice(attr, keys)


class HStoreManager(HStoreManagerMixin, ExpressionManagerMixin, models.Manager):
    def get_query_set(self):
        return HStoreQueryset(self.model, using=self._db)


# Signal attaching
from psycopg2.extras import register_hstore

def register_hstore_handler(connection, **kwargs):
    register_hstore(connection.cursor(), globally=True, unicode=True)

from djorm_core.models import connection_handler
connection_handler.attach_handler(register_hstore_handler, vendor="postgresql", unique=True)
