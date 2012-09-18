from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

class BaseFilter(object):
    title = None  # Human-readable title to appear in the right sidebar.
    
    def __init__(self, section):
        self.section = section
        self.resource = section.resource
        self.changelist = section.changelist
        if self.title is None:
            raise ImproperlyConfigured(
                "The filter '%s' does not specify "
                "a 'title'." % self.__class__.__name__)
    
    def make_link(self, **kwargs):
        return self.section.make_link(**kwargs)
    
    def populate_state(self, state):
        pass
    
    def get_links(self, state):
        """
        Returns links representing the filterable actions.
        """
        return []
    
    def filter_index(self, state, active_index):
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
    
    def is_active(self, state):
        return False

class BaseChoicesFilter(BaseFilter):
    def get_links(self, state):
        pass #TODO take choices and return links
    
    def choices(self, state):
        return []

class SimpleFilter(BaseChoicesFilter):
    # The parameter that should be used in the query string for that filter.
    parameter_name = None

    def __init__(self, section):
        super(SimpleFilter, self).__init__(section)
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
    
    def choices(self, state):
        yield {
            'selected': self.value() is None,
            'query_string': state.get_query_string({}, [self.parameter_name]),
            'display': _('All'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': state.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

