================
djorm-ext-hstore
================

Is the library which integrates the `hstore`_ extension of PostgreSQL into Django,

Compatible with django: 1.4 and posible with 1.3. Django 1.5 and python3.2+ compatibility coming soon.

Limitations and notes
---------------------

- PostgreSQL's implementation of hstore has no concept of type; it stores a mapping of string keys to
  string values. This library makes no attempt to coerce keys or values to strings.


Classes
-------

The library provides three principal classes:

``djorm_hstore.fields.DictionaryField``
    An ORM field which stores a mapping of string key/value pairs in an hstore column.
``djorm_hstore.fields.ReferencesField``
    An ORM field which builds on DictionaryField to store a mapping of string keys to
    django object references, much like ForeignKey.
``djorm_hstor.models.HStoreManager``
    An ORM manager which provides much of the query functionality of the library.

**NOTE**: the predefined hstore manager inherits all functionality of djorm-ext-expressions module (which is part of django orm extensions package)


Usage
-----

Initially define some sample model:

.. code-block:: python

    from django.db import models
    from djorm_hstore.fields import DictionaryField
    from djorm_hstore.models import HStoreManager

    class Something(models.Model):
        name = models.CharField(max_length=32)
        data = DictionaryField(db_index=True)
        objects = HStoreManager()

        def __unicode__(self):
            return self.name


You then treat the ``data`` field as simply a dictionary of string pairs:

.. code-block:: python

    instance = Something.objects.create(name='something', data={'a': '1', 'b': '2'})
    assert instance.data['a'] == '1'

    empty = Something.objects.create(name='empty')
    assert empty.data == {}

    empty.data['a'] = '1'
    empty.save()
    assert Something.objects.get(name='something').data['a'] == '1'


You can issue indexed queries against hstore fields:


.. code-block:: python

    from djorm_hstore.expressions import HstoreExpression as HE

    # equivalence
    Something.objects.filter(data={'a': '1', 'b': '2'})

    # subset by key/value mapping
    Something.objects.where(HE("data").contains({'a':'1'}))

    # subset by list of keys
    Something.objects.where(HE("data").contains(['a', 'b']))

    # subset by single key
    Something.objects.where(HE("data").contains("a"))


You can also take advantage of some db-side functionality by using the manager:

.. code-block:: python

    # identify the keys present in an hstore field
    >>> Something.objects.filter(id=1).hkeys(attr='data')
    ['a', 'b']

    # peek at a a named value within an hstore field
    >>> Something.objects.filter(id=1).hpeek(attr='data', key='a')
    '1'

    # remove a key/value pair from an hstore field
    >>> Something.objects.filter(name='something').hremove('data', 'b')


In addition to filters and specific methods to retrieve keys or hstore field values,
we can also use annotations, and then we can filter for them.

.. code-block:: python

    from djorm_hstore.functions import HstoreSlice, HstorePeek, HstoreKeys

    queryset = SomeModel.objects.annotate_functions(
        sliced = HstoreSlice("hstorefield", ['v']),
        peeked = HstorePeek("hstorefield", "v"),
        keys = HstoreKeys("hstorefield"),
    )
