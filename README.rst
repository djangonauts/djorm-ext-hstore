================
djorm-ext-hstore
================

Is the library which integrates the hstore extension of PostgreSQL into Django,

Compatible with:

* django: 1.4, 1.5, 1.6
* python: 2.7 y 3.3+


Limitations and notes
---------------------

- PostgreSQL's implementation of hstore has no concept of type; it stores a mapping of string keys to
  string values. This library makes no attempt to coerce keys or values to strings.
- Hstore extension is not automatically installed on use this package. You must install it manually. (For execute tests, you must install hstore extension on template1 database.

- For run tests, hstore extension must be installed on template1 database. (Short version)


Limitation for running tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This limitatation is affects bugs #11 and #12 (and can not be solved with other aproach
than installing hstore on template1 database.

The complete explanation, a lot of thanks to Florian Demmer:

    i think i got it... the oid is the problem and how and when it is determined...
    and maybe a little how the tests are set up... and generally it is a multi-db issue.

    in test settings.py two databases are configured, but while running tests of course
    django creates new "test_*" databases (from "template1"). however initially django
    connects to one of the configured "test" or "test2" databases. i don't know which.
    but on this initial connect the connect-signal triggers the extension registration,
    which determines the hstore oid and uses it to register the extension globally.

    so the extension is now registerd with the oid from "test" or "test2". if one had
    added the hstore extension to "template1" before creating "test" and "test2" this
    would be no problem, as both would have the hstore oid copied from "template1".

    so in my case i did not have "template1" set up on my notebook when i created the
    test databases and both have different hstore oids and tests fail. i did have it set
    up on my pc and the test databases have the same hstore oid and test work.

    so, what does it mean!?

    using unique=False works around this problem by reloading the oid for every connection.
    the more i think about it, this is a very, very ugly workaround.


I strongly recommend install hstore on template1 for avoid strange behavior.


Classes
-------

The library provides three principal classes:

``djorm_hstore.fields.DictionaryField``
    An ORM field which stores a mapping of string key/value pairs in an hstore column.
``djorm_hstore.fields.ReferencesField``
    An ORM field which builds on DictionaryField to store a mapping of string keys to
    django object references, much like ForeignKey.
``djorm_hstore.models.HStoreManager``
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



Psycopg2 hstore registration
----------------------------

If for some reason you have to use djorm_hstore along databases that don't have
hstore extension installed, you can skip hstore registration by setting
``HAS_HSTORE`` to ``False`` in your database config:

.. code-block:: python

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'name',
            'USER': 'user',
            'PASSWORD': 'pass',
            'HOST': 'localhost',
            'PORT': '',
        },
        'other': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'other',
            'USER': 'user',
            'PASSWORD': 'pass',
            'HOST': 'localhost',
            'PORT': '',
            'HAS_HSTORE': False,
        }
    }

If you do that, then don't try to create ``DictionaryField`` in this database.
Be sure to check out allow_syncdb_ documentation.

.. _allow_syncdb: https://docs.djangoproject.com/en/1.5/topics/db/multi-db/#allow_syncdb
