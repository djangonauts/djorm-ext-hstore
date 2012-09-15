# -*- coding: utf-8 -*-

from djorm_expressions.base import SqlFunction


class HstoreSlice(SqlFunction):
    """
    Obtain dictionary with only selected keys.

    Usage example::

        queryset = SomeModel.objects\
            .inline_annotate(sliced=HstoreSlice("data").as_aggregate(['v']))
    """

    sql_template = '%(function)s(%(field)s, %%s)'
    sql_function = 'slice'


class HstorePeek(SqlFunction):
    """
    Obtain values from hstore field.
    Usage example::

        queryset = SomeModel.objects\
            .inline_annotate(peeked=HstorePeek("data").as_aggregate("v"))
    """

    sql_template = '%(field)s -> %%s'


class HstoreKeys(SqlFunction):
    """
    Obtain keys from hstore fields.
    Usage::

        queryset = SomeModel.objects\
            .inline_annotate(keys=HstoreKeys("somefield").as_aggregate())
    """

    sql_function = 'akeys'
