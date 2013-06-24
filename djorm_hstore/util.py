# -*- coding: utf-8 -*-

from django.core.exceptions import ObjectDoesNotExist

import sys

if sys.version_info[0] == 3:
    string_type = str
    bytes_type = bytes
    basestring = (str,)

else:
    string_type = unicode
    bytes_type = str
    basestring = (str, unicode)


def acquire_reference(reference):
    try:
        implementation, identifier = reference.split(':')
        module, sep, attr = implementation.rpartition('.')
        implementation = getattr(__import__(module, fromlist=(attr,)), attr)
        return implementation.objects.get(pk=identifier)
    except ObjectDoesNotExist:
        return None
    except Exception:
        raise ValueError


def identify_instance(instance):
    implementation = type(instance)
    return '%s.%s:%s' % (implementation.__module__, implementation.__name__, instance.pk)


def serialize_references(references):
    refs = {}
    for key, instance in references.items():
        if not isinstance(instance, basestring):
            refs[key] = identify_instance(instance)
        else:
            refs[key] = instance
    else:
        return refs


def unserialize_references(references):
    refs = {}
    for key, reference in references.items():
        if isinstance(reference, basestring):
            refs[key] = acquire_reference(reference)
        else:
            refs[key] = reference
    else:
        return refs
