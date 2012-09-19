from django.utils.datastructures import SortedDict

class ChangeList(object):
    ordering = None
    paginator_class = None #default to resource.get_paginator
    
    def __init__(self, resource):
        self.resource = resource
        self.sections = SortedDict()
    
    def detect_sections(self):
        pass
    
    def populate_state(self, state):
        for section in self.sections.itervalues():
            section.populate_state(state)
        index = self.get_instances(state)
        state['paginator'] = self.get_paginator(index)
    
    def make_link(self, lookup_params, **kwargs):
        pass #TODO

    def register_section(self, name, filter_section, **kwargs):
        kwargs.update({'name':name,
                       'changelist':self,
                       'resource':self.resource,})
        self.sections[name] = filter_section(**kwargs)
        return self.sections[name]
    
    def get_active_index(self, state):
        return self.resource.get_active_index(state=state)
    
    def get_instances(self, state):
        assert 'filter_params' in state, 'Filters need to know what params they are operating off'
        active_index = self.get_active_index(state)
        for section in self.sections.itervalues():
            active_index = section.filter_index(state, active_index)
        return active_index
    
    def get_links(self, state):
        links = list()
        for section in self.sections.itervalues():
            links.extend(section.get_links(state, rel=section.name))
        return links
    
    def get_paginator_kwargs(self):
        return {}
    
    def get_paginator(self, index, **kwargs):
        kwargs.update(self.get_paginator_kwargs())
        if self.paginator_class:
            return self.paginator_class(index, **kwargs)
        return self.resource.get_paginator(index, **kwargs)
    
    def get_ordering(self):
        if self.ordering is not None:
            return self.ordering
        return self.resurce.get_ordering()

class FilterSection(object):
    def __init__(self, name, changelist, resource):
        self.name = name
        self.changelist = changelist
        self.resource = resource
        self.filters = list()
    
    def register_filter(self, a_filter, **kwargs):
        kwargs['section'] = self
        self.filters.append(a_filter(**kwargs))
    
    def make_link(self, lookup_params, **kwargs):
        return self.changelist.make_link(lookup_params, **kwargs)
    
    def populate_state(self, state):
        assert 'filter_params' in state, 'Filters need to know what params they are operating off'
        for a_filter in self.filters:
            a_filter.populate_state(state)
    
    def get_links(self, state):
        links = list()
        for a_filter in self.filters:
            links.extend(a_filter.get_links(state))
        return links
    
    def filter_index(self, state, active_index):
        for a_filter in self.filters:
            if a_filter.is_active(state):
                new_index = a_filter.filter_index(state, active_index)
                if new_index is not None:
                    active_index = new_index
        return active_index

