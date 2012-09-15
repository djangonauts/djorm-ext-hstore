# -*- coding: utf-8 -*-

from django.db import transaction
from django.db.models.sql.subqueries import UpdateQuery

def select_query(method):
    def selector(self, *args, **params):
        query = self.query.clone()
        query.default_cols = False
        query.clear_select_fields()
        return method(self, query, *args, **params)
    return selector


def update_query(method):
    def updater(self, *args, **params):
        self._for_write = True
        temporal_update_query = self.query.clone(UpdateQuery)
        query = method(self, temporal_update_query, *args, **params)

        forced_managed = False
        if not transaction.is_managed(using=self.db):
            transaction.enter_transaction_management(using=self.db)
            forced_managed = True

        try:
            rows = query.get_compiler(self.db).execute_sql(None)
            if forced_managed:
                transaction.commit(using=self.db)
            else:
                transaction.commit_unless_managed(using=self.db)
        finally:
            if forced_managed:
                transaction.leave_transaction_management(using=self.db)

        self._result_cache = None
        return rows

    updater.alters_data = True
    return updater
