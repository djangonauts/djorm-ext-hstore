# -*- coding: utf-8 -*-

from django.db import connections
from django.db.models.aggregates import Count
from django.utils.unittest import TestCase

from ..functions import HstoreKeys, HstoreSlice, HstorePeek
from ..expressions import HstoreExpression

from .models import DataBag, Ref, RefsBag

class TestDictionaryField(TestCase):
    def setUp(self):
        DataBag.objects.all().delete()

    def _create_bags(self):
        alpha = DataBag.objects.create(name='alpha', data={'v': '1', 'v2': '3'})
        beta = DataBag.objects.create(name='beta', data={'v': '2', 'v2': '4'})
        return alpha, beta

    def _create_bitfield_bags(self):
        # create dictionaries with bits as dictionary keys (i.e. bag5 = { 'b0':'1', 'b2':'1'})
        for i in xrange(10):
            DataBag.objects.create(name='bag%d' % (i,),
               data=dict(('b%d' % (bit,), '1') for bit in xrange(4) if (1 << bit) & i))

    def test_regression_handler(self):
        self._create_bags()
        from django.db import connection
        connection.close()

        obj = DataBag.objects.get(name="alpha")


    def test_empty_instantiation(self):
        bag = DataBag.objects.create(name='bag')
        self.assertTrue(isinstance(bag.data, dict))
        self.assertEqual(bag.data, {})

    def test_named_querying(self):
        alpha, beta = self._create_bags()

        instance = DataBag.objects.get(name='alpha')
        self.assertEqual(instance, alpha)

        instance = DataBag.objects.filter(name='beta')[0]
        self.assertEqual(instance, beta)

    def test_annotations(self):
        self._create_bitfield_bags()
        queryset = DataBag.objects\
            .annotate(num_id=Count('id'))\
            .filter(num_id=1)

        self.assertEqual(queryset[0].num_id, 1)

    def test_unicode_processing(self):
        greets = {
            u'de': u'Gr\xfc\xdfe, Welt',
            u'en': u'hello, world',
            u'es': u'hola, ma\xf1ana',
            u'he': u'\u05e9\u05dc\u05d5\u05dd, \u05e2\u05d5\u05dc\u05dd',
            u'jp': u'\u3053\u3093\u306b\u3061\u306f\u3001\u4e16\u754c',
            u'zh': u'\u4f60\u597d\uff0c\u4e16\u754c',
        }
        DataBag.objects.create(name='multilang', data=greets)

        instance = DataBag.objects.get(name='multilang')
        self.assertEqual(greets, instance.data)

    def test_query_escaping(self):
        me = self
        def readwrite(s):
            # try create and query with potentially illegal characters in the field and dictionary key/value
            o = DataBag.objects.create(name=s, data={ s: s })
            me.assertEqual(o, DataBag.objects.get(name=s, data={ s: s }))

        readwrite('\' select')
        readwrite('% select')
        readwrite('\\\' select')
        readwrite('-- select')
        readwrite('\n select')
        readwrite('\r select')
        readwrite('* select')

    def test_replace_full_dictionary(self):
        DataBag.objects.create(name='foo', data={ 'change': 'old value', 'remove': 'baz'})

        replacement = { 'change': 'new value', 'added': 'new'}
        DataBag.objects.filter(name='foo').update(data=replacement)

        instance = DataBag.objects.get(name='foo')
        self.assertEqual(replacement, instance.data)

    def test_equivalence_querying(self):
        alpha, beta = self._create_bags()

        for bag in (alpha, beta):
            data = {'v': bag.data['v'], 'v2': bag.data['v2']}

            instance = DataBag.objects.get(data=data)
            self.assertEqual(instance, bag)

            r = DataBag.objects.filter(data=data)
            self.assertEqual(len(r), 1)
            self.assertEqual(r[0], bag)

    def test_hkeys(self):
        alpha, beta = self._create_bags()

        instance = DataBag.objects.filter(id=alpha.id)
        self.assertEqual(instance.hkeys('data'), ['v', 'v2'])

        instance = DataBag.objects.filter(id=beta.id)
        self.assertEqual(instance.hkeys('data'), ['v', 'v2'])

    def test_hkeys_annotation(self):
        alpha, beta = self._create_bags()
        queryset = DataBag.objects.annotate_functions(keys=HstoreKeys("data"))
        self.assertEqual(queryset[0].keys, ['v', 'v2'])
        self.assertEqual(queryset[1].keys, ['v', 'v2'])

    def test_hpeek(self):
        alpha, beta = self._create_bags()

        queryset = DataBag.objects.filter(id=alpha.id)
        self.assertEqual(queryset.hpeek(attr='data', key='v'), '1')
        self.assertEqual(queryset.hpeek(attr='data', key='invalid'), None)

    def test_hpeek_annotation(self):
        alpha, beta = self._create_bags()
        queryset = DataBag.objects.annotate_functions(peeked=HstorePeek("data", "v"))
        self.assertEqual(queryset[0].peeked, "1")
        self.assertEqual(queryset[1].peeked, "2")

    def test_hremove(self):
        alpha, beta = self._create_bags()

        instance = DataBag.objects.get(name='alpha')
        self.assertEqual(instance.data, alpha.data)

        DataBag.objects.filter(name='alpha').hremove('data', 'v2')
        instance = DataBag.objects.get(name='alpha')
        self.assertEqual(instance.data, {'v': '1'})

        instance = DataBag.objects.get(name='beta')
        self.assertEqual(instance.data, beta.data)

        DataBag.objects.filter(name='beta').hremove('data', ['v', 'v2'])
        instance = DataBag.objects.get(name='beta')
        self.assertEqual(instance.data, {})

    def test_hslice(self):
        alpha, beta = self._create_bags()

        queryset = DataBag.objects.filter(id=alpha.id)
        self.assertEqual(queryset.hslice(attr='data', keys=['v']), {'v': '1'})
        self.assertEqual(queryset.hslice(attr='data', keys=['invalid']), {})

    def test_hslice_annotation(self):
        alpha, beta = self._create_bags()
        queryset = DataBag.objects.annotate_functions(sliced=HstoreSlice("data", ['v']))

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].sliced, {'v': '1'})

    def test_hupdate(self):
        alpha, beta = self._create_bags()
        self.assertEqual(DataBag.objects.get(name='alpha').data, alpha.data)
        DataBag.objects.filter(name='alpha').hupdate('data', {'v2': '10', 'v3': '20'})
        self.assertEqual(DataBag.objects.get(name='alpha').data, {'v': '1', 'v2': '10', 'v3': '20'})

    def test_key_value_subset_querying(self):
        alpha, beta = self._create_bags()

        for bag in (alpha, beta):
            qs = DataBag.objects.where(
                HstoreExpression("data").contains({'v': bag.data['v']})
            )

            self.assertEqual(len(qs), 1)
            self.assertEqual(qs[0], bag)

            qs = DataBag.objects.where(
                HstoreExpression("data").contains({'v': bag.data['v'], 'v2': bag.data['v2']})
            )
            self.assertEqual(len(qs), 1)
            self.assertEqual(qs[0], bag)

    def test_multiple_key_subset_querying(self):
        alpha, beta = self._create_bags()

        for keys in (['v'], ['v', 'v2']):
            qs = DataBag.objects.where(
                HstoreExpression("data").contains(keys)
            )
            self.assertEqual(qs.count(), 2)

        for keys in (['v', 'nv'], ['n1', 'n2']):
            qs = DataBag.objects.where(
                HstoreExpression("data").contains(keys)
            )
            self.assertEqual(qs.count(), 0)

    def test_single_key_querying(self):
        alpha, beta = self._create_bags()
        for key in ('v', 'v2'):
            qs = DataBag.objects.where(HstoreExpression("data").contains(key))
            self.assertEqual(qs.count(), 2)

        for key in ('n1', 'n2'):
            qs = DataBag.objects.where(HstoreExpression("data").contains(key))
            self.assertEqual(qs.count(), 0)

    def test_nested_filtering(self):
        self._create_bitfield_bags()

        # Test cumulative successive filters for both dictionaries and other fields
        qs = DataBag.objects.all()
        self.assertEqual(10, qs.count())

        qs = qs.where(HstoreExpression("data").contains({'b0':'1'}))
        self.assertEqual(5, qs.count())

        qs = qs.where(HstoreExpression("data").contains({'b1':'1'}))
        self.assertEqual(2, qs.count())

        qs = qs.filter(name='bag3')
        self.assertEqual(1, qs.count())

    def test_aggregates(self):
        self._create_bitfield_bags()
        res = DataBag.objects.where(HstoreExpression("data").contains({'b0':'1'}))\
            .aggregate(Count('id'))

        self.assertEqual(res['id__count'], 5)

    def test_empty_querying(self):
        bag = DataBag.objects.create(name='bag')
        self.assertTrue(DataBag.objects.get(data={}))
        self.assertTrue(DataBag.objects.filter(data={}))
        self.assertTrue(DataBag.objects.where(HstoreExpression("data").contains({})))


class TestReferencesField(TestCase):
    def setUp(self):
        Ref.objects.all().delete()
        RefsBag.objects.all().delete()

    def _create_bags(self):
        refs = [Ref.objects.create(name=str(i)) for i in range(4)]
        alpha = RefsBag.objects.create(name='alpha', refs={'0': refs[0], '1': refs[1]})
        beta = RefsBag.objects.create(name='beta', refs={'0': refs[2], '1': refs[3]})
        return alpha, beta, refs

    def test_empty_instantiation(self):
        bag = RefsBag.objects.create(name='bag')
        self.assertTrue(isinstance(bag.refs, dict))
        self.assertEqual(bag.refs, {})

    def test_equivalence_querying(self):
        alpha, beta, refs = self._create_bags()
        for bag in (alpha, beta):
            refs = {'0': bag.refs['0'], '1': bag.refs['1']}
            self.assertEqual(RefsBag.objects.get(refs=refs), bag)
            r = RefsBag.objects.filter(refs=refs)
            self.assertEqual(len(r), 1)
            self.assertEqual(r[0], bag)

    def test_hkeys(self):
        alpha, beta, refs = self._create_bags()
        self.assertEqual(RefsBag.objects.filter(id=alpha.id).hkeys(attr='refs'), ['0', '1'])

    def test_hpeek(self):
        alpha, beta, refs = self._create_bags()
        self.assertEqual(RefsBag.objects.filter(id=alpha.id).hpeek(attr='refs', key='0'), refs[0])
        self.assertEqual(RefsBag.objects.filter(id=alpha.id).hpeek(attr='refs', key='invalid'), None)

    def test_hslice(self):
        alpha, beta, refs = self._create_bags()
        self.assertEqual(RefsBag.objects.filter(id=alpha.id).hslice(attr='refs', keys=['0']), {'0': refs[0]})
        self.assertEqual(RefsBag.objects.filter(id=alpha.id).hslice(attr='refs', keys=['invalid']), {})

    def test_empty_querying(self):
        bag = RefsBag.objects.create(name='bag')
        self.assertTrue(RefsBag.objects.get(refs={}))
        self.assertTrue(RefsBag.objects.filter(refs={}))

    # TODO: fix this test
    #def test_key_value_subset_querying(self):
    #    alpha, beta, refs = self._create_bags()
    #    for bag in (alpha, beta):
    #        qs = RefsBag.objects.where(
    #            HstoreExpression("refs").contains({'0': bag.refs['0']})
    #        )
    #        self.assertEqual(len(qs), 1)
    #        self.assertEqual(qs[0], bag)

    #        qs = RefsBag.objects.where(
    #            HstoreExpression("refs").contains({'0': bag.refs['0'], '1': bag.refs['1']})
    #        )

    #        self.assertEqual(len(qs), 1)
    #        self.assertEqual(qs[0], bag)

    def test_multiple_key_subset_querying(self):
        alpha, beta, refs = self._create_bags()

        for keys in (['0'], ['0', '1']):
            qs = RefsBag.objects.where(HstoreExpression("refs").contains(keys))
            self.assertEqual(qs.count(), 2)

        for keys in (['0', 'nv'], ['n1', 'n2']):
            qs = RefsBag.objects.where(HstoreExpression("refs").contains(keys))
            self.assertEqual(qs.count(), 0)

    def test_single_key_querying(self):
        alpha, beta, refs = self._create_bags()
        for key in ('0', '1'):
            qs = RefsBag.objects.where(HstoreExpression("refs").contains(key))
            self.assertEqual(qs.count(), 2)

        for key in ('n1', 'n2'):
            qs = RefsBag.objects.where(HstoreExpression("refs").contains(key))
            self.assertEqual(qs.count(), 0)

