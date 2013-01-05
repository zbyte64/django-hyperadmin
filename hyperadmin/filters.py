from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode

class BaseFilter(object):
    title = None  # Human-readable title to appear in the right sidebar.
    
    def __init__(self, index):
        self.index = index
        self.resource = index.resource
        if self.title is None:
            raise ImproperlyConfigured(
                "The filter '%s' does not specify "
                "a 'title'." % self.__class__.__name__)
    
    @property
    def state(self):
        return self.resource.state
    
    def make_link(self, **kwargs):
        return self.index.get_link(**kwargs)
    
    def populate_state(self):
        pass
    
    def get_links(self, **link_kwargs):
        """
        Returns links representing the filterable actions.
        """
        return []
    
    def filter_index(self, active_index):
        """
        Returns the filtered queryset.
        """
        raise NotImplementedError
    
    def expected_parameters(self):
        """
        Returns the list of parameter names that are expected from the
        request's query string and that will be used by this filter.
        """
        raise NotImplementedError
    
    def is_active(self):
        return False
    
    def values(self):
        vals = list()
        filter_params = self.state.params
        for param in self.expected_parameters():
            vals.append(filter_params.get(param, None))
        return vals

class BaseChoicesFilter(BaseFilter):
    def get_links(self, **link_kwargs):
        links = list()
        for choice in self.choices():
            kwargs = dict(link_kwargs)
            classes = kwargs.get('classes', [])
            kwargs['group'] = self.title
            kwargs['classes'] = classes
            if choice.get('selected', False):
                classes.append('selected')
            #CONSIDER prompt may want to include group if not supported
            kwargs['prompt'] = force_unicode(choice['display'])
            kwargs['url'] = u'./' + choice['query_string']
            links.append(self.make_link(**kwargs))
        return links
    
    def choices(self):
        return []

class SimpleFilter(BaseChoicesFilter):
    # The parameter that should be used in the query string for that filter.
    parameter_name = None

    def __init__(self, index):
        super(SimpleFilter, self).__init__(index)
        if self.parameter_name is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify "
                "a 'parameter_name'." % self.__class__.__name__)
        lookup_choices = self.lookups()
        if lookup_choices is None:
            lookup_choices = ()
        self.lookup_choices = list(lookup_choices)

    def has_output(self):
        return len(self.lookup_choices) > 0

    def value(self):
        """
        Returns the value (in string format) provided in the request's
        query string for this filter, if any. If the value wasn't provided then
        returns None.
        """
        return self.used_parameters.get(self.parameter_name, None)

    def lookups(self):
        """
        Must be overriden to return a list of tuples (value, verbose value)
        """
        raise NotImplementedError

    def expected_parameters(self):
        return [self.parameter_name]
    
    def choices(self):
        yield {
            'selected': self.value() is None,
            'query_string': self.state.get_query_string({}, [self.parameter_name]),
            'display': _('All'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': self.state.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

