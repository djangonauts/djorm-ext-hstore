# -*- coding: utf-8 -*-

import sys
if sys.version_info[0] > 2:
    basestring = str

from djorm_expressions.base import SqlExpression

class HstoreExpression(object):
    def __init__(self, field):
        self.field = field

    def contains(self, value):
        if isinstance(value, dict):
            expression = SqlExpression(
                self.field, "@>", value
            )
        elif isinstance(value, (list,tuple)):
            expression = SqlExpression(
                self.field, "?&", value
            )
        elif isinstance(value, basestring):
            expression = SqlExpression(
                self.field, "?", value
            )
        else:
            raise ValueError("Invalid value")
        return expression

    def exact(self, value):
        return SqlExpression(
            self.field, "=", value
        )

    def as_sql(self, qn, queryset):
        raise NotImplementedError
