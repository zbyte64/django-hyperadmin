import datetime
import operator

from django.db import models
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
try:
    from django.utils import timezone
except ImportError:
    import pytz as timezone
from django.contrib.admin.util import (get_model_from_relation,
    reverse_field_path, get_limit_choices_to_from_path, )
try:
    from django.contrib.admin.util import lookup_needs_distinct, prepare_lookup_value
except ImportError:
    from hyperadmin.resources.models.util import lookup_needs_distinct, prepare_lookup_value

from hyperadmin.filters import BaseChoicesFilter, BaseFilter

SEARCH_VAR = 'q'

class SearchFilter(BaseFilter):
    title = _('Search')
    
    def __init__(self, index, search_fields):
        super(SearchFilter, self).__init__(index)
        self.search_fields = search_fields
    
    def value(self):
        return self.state.params.get(SEARCH_VAR, '')
    
    def is_active(self):
        return bool(self.value())
    
    def filter_index(self, active_index):
        use_distinct = False
        query = self.value()
        
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        if self.search_fields and query:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in self.search_fields]
            for bit in query.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                active_index = active_index.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(self.resource.opts, search_spec):
                        use_distinct = True
                        break
        if use_distinct:
            return active_index.distinct()
        return active_index

class FieldFilter(BaseChoicesFilter):
    _field_list_filters = []
    _take_priority_index = 0

    def __init__(self, field, field_path, index):
        self.field = field
        self.field_path = field_path
        self.title = getattr(field, 'verbose_name', field_path)
        self.used_parameters = dict()
        super(FieldFilter, self).__init__(index)

    def is_active(self):
        return bool(self.used_parameters)
    
    def populate_state(self):
        params = self.state.params.copy()
        self.used_parameters = dict()
        for p in self.expected_parameters():
            if p in params:
                value = params[p]
                self.used_parameters[p] = prepare_lookup_value(p, value)

    def filter_index(self, active_index):
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
    def create(cls, field, field_path, index):
        for test, list_filter_class in cls._field_list_filters:
            if not test(field):
                continue
            return list_filter_class(field, field_path, index)


class RelatedFieldFilter(FieldFilter):
    def __init__(self, field, field_path, index):
        other_model = get_model_from_relation(field)
        rel_name = other_model._meta.pk.name
        self.lookup_kwarg = '%s__%s__exact' % (field_path, rel_name)
        self.lookup_kwarg_isnull = '%s__isnull' % field_path
        self.lookup_choices = field.get_choices(include_blank=False)
        super(RelatedFieldFilter, self).__init__(
            field, field_path, index)
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
    
    def is_active(self):
        if not self.has_output():
            return False
        return super(RelatedFieldFilter, self).is_active()

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]
    
    def choices(self):
        from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
        lookup_val, lookup_val_isnull = self.values()
        yield {
            'selected': lookup_val is None and not lookup_val_isnull,
            'query_string': self.state.get_query_string({},
                [self.lookup_kwarg, self.lookup_kwarg_isnull]),
            'display': _('All'),
        }
        for pk_val, val in self.lookup_choices:
            yield {
                'selected': lookup_val == smart_unicode(pk_val),
                'query_string': self.state.get_query_string({
                    self.lookup_kwarg: pk_val,
                }, [self.lookup_kwarg_isnull]),
                'display': val,
            }
        if (isinstance(self.field, models.related.RelatedObject)
                and self.field.field.null or hasattr(self.field, 'rel')
                    and self.field.null):
            yield {
                'selected': bool(lookup_val_isnull),
                'query_string': self.state.get_query_string({
                    self.lookup_kwarg_isnull: 'True',
                }, [self.lookup_kwarg]),
                'display': EMPTY_CHANGELIST_VALUE,
            }

FieldFilter.register(lambda f: (
        hasattr(f, 'rel') and bool(f.rel) or
        isinstance(f, models.related.RelatedObject)), RelatedFieldFilter)


class BooleanFieldFilter(FieldFilter):
    def __init__(self, field, field_path, index):
        self.lookup_kwarg = '%s__exact' % field_path
        self.lookup_kwarg2 = '%s__isnull' % field_path
        super(BooleanFieldFilter, self).__init__(field, field_path, index)

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg2]

    def choices(self):
        lookup_val, lookup_val2 = self.values()
        for lookup, title in (
                (None, _('All')),
                ('1', _('Yes')),
                ('0', _('No'))):
            yield {
                'selected': lookup_val == lookup and not lookup_val2,
                'query_string': self.state.get_query_string({
                        self.lookup_kwarg: lookup,
                    }, [self.lookup_kwarg2]),
                'display': title,
            }
        if isinstance(self.field, models.NullBooleanField):
            yield {
                'selected': lookup_val2 == 'True',
                'query_string': self.state.get_query_string({
                        self.lookup_kwarg2: 'True',
                    }, [self.lookup_kwarg]),
                'display': _('Unknown'),
            }

FieldFilter.register(lambda f: isinstance(f,
    (models.BooleanField, models.NullBooleanField)), BooleanFieldFilter)


class ChoicesFieldFilter(FieldFilter):
    def __init__(self, field, field_path, index):
        self.lookup_kwarg = '%s__exact' % field_path
        super(ChoicesFieldFilter, self).__init__(
            field, field_path, index)

    def expected_parameters(self):
        return [self.lookup_kwarg]

    def choices(self):
        lookup_val = self.values()[0]
        yield {
            'selected': lookup_val is None,
            'query_string': self.state.get_query_string({}, [self.lookup_kwarg]),
            'display': _('All')
        }
        for lookup, title in self.field.flatchoices:
            yield {
                'selected': smart_unicode(lookup) == lookup_val,
                'query_string': self.state.get_query_string({
                                    self.lookup_kwarg: lookup}),
                'display': title,
            }

FieldFilter.register(lambda f: bool(f.choices), ChoicesFieldFilter)


class DateFieldFilter(FieldFilter):
    def __init__(self, field, field_path, index):
        now = datetime.datetime.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        #if now.tzinfo is not None:
        #    current_tz = timezone.get_current_timezone()
        #    now = now.astimezone(current_tz)
        #    if hasattr(current_tz, 'normalize'):
        #        # available for pytz time zones
        #        now = current_tz.normalize(now)

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
            field, field_path, index)
    
    def populate_state(self):
        params = self.state.params
        self.field_generic = '%s__' % self.field_path
        self.date_params = dict([(k, v) for k, v in params.items()
                                 if k.startswith(self.field_generic)])
        self.used_parameters = self.date_params

    def expected_parameters(self):
        return [self.lookup_kwarg_since, self.lookup_kwarg_until]

    def choices(self):
        for title, param_dict in self.links:
            yield {
                'selected': self.date_params == param_dict,
                'query_string': self.state.get_query_string(
                                    param_dict, [self.field_generic]),
                'display': title,
            }

FieldFilter.register(
    lambda f: isinstance(f, models.DateField), DateFieldFilter)


# This should be registered last, because it's a last resort. For example,
# if a field is eligible to use the BooleanFieldFilter, that'd be much
# more appropriate, and the AllValuesFieldFilter won't get used for it.
class AllValuesFieldFilter(FieldFilter):
    def __init__(self, field, field_path, index):
        super(AllValuesFieldFilter, self).__init__(
            field, field_path, index)
        
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

    def choices(self):
        lookup_val, lookup_val_isnull = self.values()
        from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
        yield {
            'selected': (lookup_val is None
                and lookup_val_isnull is None),
            'query_string': self.state.get_query_string({},
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
                'selected': lookup_val == val,
                'query_string': self.state.get_query_string({
                    self.lookup_kwarg: val,
                }, [self.lookup_kwarg_isnull]),
                'display': val,
            }
        if include_none:
            yield {
                'selected': bool(lookup_val_isnull),
                'query_string': self.state.get_query_string({
                    self.lookup_kwarg_isnull: 'True',
                }, [self.lookup_kwarg]),
                'display': EMPTY_CHANGELIST_VALUE,
            }

FieldFilter.register(lambda f: True, AllValuesFieldFilter)
