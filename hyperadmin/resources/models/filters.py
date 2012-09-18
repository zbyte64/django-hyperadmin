import datetime

from django.db import models
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.contrib.admin.util import (get_model_from_relation,
    reverse_field_path, get_limit_choices_to_from_path, prepare_lookup_value)

from hyperadmin.resources.crud.filters import BaseChoicesFilter

class FieldFilter(BaseChoicesFilter):
    _field_list_filters = []
    _take_priority_index = 0

    def __init__(self, field, field_path, section):
        self.field = field
        self.field_path = field_path
        self.title = getattr(field, 'verbose_name', field_path)
        self.used_parameters = dict()
        super(FieldFilter, self).__init__(section)

    def is_active(self, state):
        return bool(self.used_parameters)
    
    def populate_state(self, state):
        params = state['lookup_params']
        self.used_parameters = dict()
        for p in self.expected_parameters():
            if p in params:
                value = params.pop(p)
                self.used_parameters[p] = prepare_lookup_value(p, value)

    def filter_index(self, state, active_index):
        return active_index.filter(**self.used_parameters)
    
    @classmethod
    def register(cls, test, list_filter_class, take_priority=False):
        if take_priority:
            # This is to allow overriding the default filters for certain types
            # of fields with some custom filters. The first found in the list
            # is used in priority.
            cls._field_list_filters.insert(
                cls._take_priority_index, (test, list_filter_class))
            cls._take_priority_index += 1
        else:
            cls._field_list_filters.append((test, list_filter_class))

    @classmethod
    def create(cls, field, request, params, model, model_admin, field_path):
        for test, list_filter_class in cls._field_list_filters:
            if not test(field):
                continue
            return list_filter_class(field, request, params,
                model, model_admin, field_path=field_path)


class RelatedFieldFilter(FieldFilter):
    def __init__(self, field, field_path, section):
        other_model = get_model_from_relation(field)
        rel_name = other_model._meta.pk.name
        self.lookup_kwarg = '%s__%s__exact' % (field_path, rel_name)
        self.lookup_kwarg_isnull = '%s__isnull' % field_path
        self.lookup_choices = field.get_choices(include_blank=False)
        super(RelatedFieldFilter, self).__init__(
            field, field_path, section)
        if hasattr(field, 'verbose_name'):
            self.lookup_title = field.verbose_name
        else:
            self.lookup_title = other_model._meta.verbose_name
        self.title = self.lookup_title

    def has_output(self):
        if (isinstance(self.field, models.related.RelatedObject)
                and self.field.field.null or hasattr(self.field, 'rel')
                    and self.field.null):
            extra = 1
        else:
            extra = 0
        return len(self.lookup_choices) + extra > 1
    
    def is_active(self, state):
        if not self.has_output():
            return False
        return super(RelatedFieldFilter, self).is_active(state)

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]
    
    def choices(self, state):
        from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
        yield {
            'selected': self.lookup_val is None and not self.lookup_val_isnull,
            'query_string': state.get_query_string({},
                [self.lookup_kwarg, self.lookup_kwarg_isnull]),
            'display': _('All'),
        }
        for pk_val, val in self.lookup_choices:
            yield {
                'selected': self.lookup_val == smart_unicode(pk_val),
                'query_string': state.get_query_string({
                    self.lookup_kwarg: pk_val,
                }, [self.lookup_kwarg_isnull]),
                'display': val,
            }
        if (isinstance(self.field, models.related.RelatedObject)
                and self.field.field.null or hasattr(self.field, 'rel')
                    and self.field.null):
            yield {
                'selected': bool(self.lookup_val_isnull),
                'query_string': state.get_query_string({
                    self.lookup_kwarg_isnull: 'True',
                }, [self.lookup_kwarg]),
                'display': EMPTY_CHANGELIST_VALUE,
            }

FieldFilter.register(lambda f: (
        hasattr(f, 'rel') and bool(f.rel) or
        isinstance(f, models.related.RelatedObject)), RelatedFieldFilter)


class BooleanFieldFilter(FieldFilter):
    def __init__(self, field, field_path, section):
        self.lookup_kwarg = '%s__exact' % field_path
        self.lookup_kwarg2 = '%s__isnull' % field_path
        super(BooleanFieldFilter, self).__init__(field, field_path, section)

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg2]

    def choices(self, cl):
        for lookup, title in (
                (None, _('All')),
                ('1', _('Yes')),
                ('0', _('No'))):
            yield {
                'selected': self.lookup_val == lookup and not self.lookup_val2,
                'query_string': cl.get_query_string({
                        self.lookup_kwarg: lookup,
                    }, [self.lookup_kwarg2]),
                'display': title,
            }
        if isinstance(self.field, models.NullBooleanField):
            yield {
                'selected': self.lookup_val2 == 'True',
                'query_string': cl.get_query_string({
                        self.lookup_kwarg2: 'True',
                    }, [self.lookup_kwarg]),
                'display': _('Unknown'),
            }

FieldFilter.register(lambda f: isinstance(f,
    (models.BooleanField, models.NullBooleanField)), BooleanFieldFilter)


class ChoicesFieldFilter(FieldFilter):
    def __init__(self, field, field_path, section):
        self.lookup_kwarg = '%s__exact' % field_path
        super(ChoicesFieldFilter, self).__init__(
            field, field_path, section)

    def expected_parameters(self):
        return [self.lookup_kwarg]

    def choices(self, cl):
        yield {
            'selected': self.lookup_val is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display': _('All')
        }
        for lookup, title in self.field.flatchoices:
            yield {
                'selected': smart_unicode(lookup) == self.lookup_val,
                'query_string': cl.get_query_string({
                                    self.lookup_kwarg: lookup}),
                'display': title,
            }

FieldFilter.register(lambda f: bool(f.choices), ChoicesFieldFilter)


class DateFieldFilter(FieldFilter):
    def __init__(self, field, field_path, section):
        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if now.tzinfo is not None:
            current_tz = timezone.get_current_timezone()
            now = now.astimezone(current_tz)
            if hasattr(current_tz, 'normalize'):
                # available for pytz time zones
                now = current_tz.normalize(now)

        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:       # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
    
        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('Any date'), {}),
            (_('Today'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('Past 7 days'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=7)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('This month'), {
                self.lookup_kwarg_since: str(today.replace(day=1)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('This year'), {
                self.lookup_kwarg_since: str(today.replace(month=1, day=1)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
        )
        super(DateFieldFilter, self).__init__(
            field, field_path, section)
    
    def populate_state(self, state):
        params = state['lookup_params']
        self.field_generic = '%s__' % self.field_path
        self.date_params = dict([(k, v) for k, v in params.items()
                                 if k.startswith(self.field_generic)])

    def expected_parameters(self):
        return [self.lookup_kwarg_since, self.lookup_kwarg_until]

    def choices(self, cl):
        for title, param_dict in self.links:
            yield {
                'selected': self.date_params == param_dict,
                'query_string': cl.get_query_string(
                                    param_dict, [self.field_generic]),
                'display': title,
            }

FieldFilter.register(
    lambda f: isinstance(f, models.DateField), DateFieldFilter)


# This should be registered last, because it's a last resort. For example,
# if a field is eligible to use the BooleanFieldFilter, that'd be much
# more appropriate, and the AllValuesFieldFilter won't get used for it.
class AllValuesFieldFilter(FieldFilter):
    def __init__(self, field, field_path, section):
        super(AllValuesFieldFilter, self).__init__(
            field, field_path, section)
        
        model = self.resource.model
        
        self.lookup_kwarg = field_path
        self.lookup_kwarg_isnull = '%s__isnull' % field_path
        parent_model, reverse_path = reverse_field_path(model, field_path)
        queryset = parent_model._default_manager.all()
        # optional feature: limit choices base on existing relationships
        # queryset = queryset.complex_filter(
        #    {'%s__isnull' % reverse_path: False})
        limit_choices_to = get_limit_choices_to_from_path(model, field_path)
        queryset = queryset.filter(limit_choices_to)

        self.lookup_choices = (queryset
                               .distinct()
                               .order_by(field.name)
                               .values_list(field.name, flat=True))
        

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]

    def choices(self, cl):
        from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
        yield {
            'selected': (self.lookup_val is None
                and self.lookup_val_isnull is None),
            'query_string': cl.get_query_string({},
                [self.lookup_kwarg, self.lookup_kwarg_isnull]),
            'display': _('All'),
        }
        include_none = False
        for val in self.lookup_choices:
            if val is None:
                include_none = True
                continue
            val = smart_unicode(val)
            yield {
                'selected': self.lookup_val == val,
                'query_string': cl.get_query_string({
                    self.lookup_kwarg: val,
                }, [self.lookup_kwarg_isnull]),
                'display': val,
            }
        if include_none:
            yield {
                'selected': bool(self.lookup_val_isnull),
                'query_string': cl.get_query_string({
                    self.lookup_kwarg_isnull: 'True',
                }, [self.lookup_kwarg]),
                'display': EMPTY_CHANGELIST_VALUE,
            }

FieldFilter.register(lambda f: True, AllValuesFieldFilter)
