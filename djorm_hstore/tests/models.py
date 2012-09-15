
from django.db import models

from ..fields import DictionaryField, ReferencesField
from ..models import HStoreManager

class Ref(models.Model):
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return self.name

    _options = {
        'manager': False,
    }

class DataBag(models.Model):
    name = models.CharField(max_length=32)
    data = DictionaryField(db_index=True)

    objects = HStoreManager()

    _options = {
        'manager': False
    }

    def __unicode__(self):
        return self.name

class RefsBag(models.Model):
    name = models.CharField(max_length=32)
    refs = ReferencesField(db_index=True)

    objects = HStoreManager()

    _options = {
        'manager': False
    }

    def __unicode__(self):
        return self.name

