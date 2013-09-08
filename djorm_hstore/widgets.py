# -*- coding: utf-8 -*-

import json

from django import forms
from django.forms import widgets
from django.contrib.admin.templatetags.admin_static import static
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


class KeyValueWidget(widgets.MultiWidget):
    input_widget_class = widgets.TextInput
    row_template = '<div class="form-row" %s>%s </div>'
    input_template = '<div class="field-box"><label for="%(label_for)s">%(label)s: %(input)s</label></div>'
    widget_template = '<ul id="%s" class="keyvaluewidget">%s</ul>'
    add_button_template = '<a href="javascript:void(0)" class="add_keyvaluewidget">' +\
                          '<img src="%(icon_url)s" width="10" height="10"> %(name)s</a>'
    remove_button_template = '<div class="field-box"><a class="inline-deletelink" href="javascript:void(0)">%s</a></div>'

    @property
    def media(self):
        return forms.Media(js=[static("djorm_hstore/js/djorm_hstore.js")])

    def __init__(self, attrs=None, key_attrs=None, value_attrs=None):
        self.key_attrs = key_attrs or {}
        self.value_attrs = value_attrs or {}
        attrs = attrs or {}
        attrs.setdefault('class', 'vTextField')
        self.attrs = attrs
        self.input_widget = self.input_widget_class(attrs)
        super(KeyValueWidget, self).__init__([], attrs)

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        main_id = self.id_for_label(final_attrs.get('id', None))
        if value:
            values = json.loads(value).items()
            empty_row = ''.join([  # row for cloning in js
                self.make_input_widget('key', name, '', main_id, '', final_attrs),
                self.make_input_widget('value', name, '', main_id, '', final_attrs),
                self.make_del_link(name, main_id, ''),
            ])
            output = [
                self.row_template % (
                    'style="display:none;"',
                    empty_row
                )
            ]
            for i, (key, val) in enumerate(values, start=1):
                output.extend(self.row_template % ('', ''.join([
                    self.make_input_widget('key', name, key, main_id, i, final_attrs),
                    self.make_input_widget('value', name, val, main_id, i, final_attrs),
                    self.make_del_link(name, main_id, i),
                ])))
            return mark_safe(self.format_output(name, main_id, output))
        return ''

    def make_input_widget(self, widget_type, name, value, main_id, index, attrs):
        id_ = '%s_%s_%s' % (main_id, widget_type, index)
        attrs = dict(attrs, id=id_, name="%s_%s_%s" % (name, widget_type, index))
        return self.input_template % {
            'label_for': id_,
            'label': _(widget_type.title()),
            'input': self.input_widget.render(name + '_%s' % index, value, attrs)
        }

    def make_del_link(self, name, main_id, index):
        return self.remove_button_template % _('Remove')

    def format_output(self, name, widget_id, rendered_widgets):
        add_button = self.add_button_template % {
            'name': _("Add another pair"),
            'icon_url': self.media.absolute_path('admin/img/icon_addlink.gif')
        }
        rendered_widgets.append(self.row_template % ('', add_button))
        html = self.widget_template % (widget_id, ''.join(rendered_widgets))
        return html

    def value_from_datadict(self, data, files, name):
        value = {}
        for key_fieldname in sorted([i for i in data if i.startswith(name + "_key_")]):
            key = data.get(key_fieldname, '')
            if not key:
                continue
            val = data.get(key_fieldname.replace('_key_', '_value_'), '')
            value[key] = val
        return json.dumps(value)

    def decompress(self, value):
        return json.loads(value).items()
