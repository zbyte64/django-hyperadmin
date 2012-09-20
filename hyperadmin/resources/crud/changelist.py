from django.utils.datastructures import SortedDict

PAGE_VAR = 'p'

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
        page_num = int(state.params.get(PAGE_VAR, 1))
        state['page'] = state['paginator'].page(page_num)
    
    def make_link(self, **kwargs):
        return self.resource.get_resource_link(**kwargs)

    def register_section(self, name, filter_section, **kwargs):
        kwargs.update({'name':name,
                       'changelist':self,
                       'resource':self.resource,})
        self.sections[name] = filter_section(**kwargs)
        return self.sections[name]
    
    def get_active_index(self):
        return self.resource.get_active_index()
    
    def get_instances(self, state):
        active_index = self.get_active_index()
        for section in self.sections.itervalues():
            active_index = section.filter_index(state, active_index)
        return active_index
    
    def get_links(self, state):
        links = list()
        for section in self.sections.itervalues():
            links.extend(section.get_links(state, rel=section.name))
        links += self.get_pagination_links(state)
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
    
    def get_pagination_links(self, state):
        links = list()
        if 'paginator' in state:
            paginator = state['paginator']
            classes = ["pagination"]
            for page in range(paginator.num_pages):
                if page == '.':
                    continue
                url = state.get_query_string({PAGE_VAR: page+1})
                links.append(self.make_link(url=url, prompt=u"%s" % page, classes=classes, rel="pagination"))
        return links

class FilterSection(object):
    def __init__(self, name, changelist, resource):
        self.name = name
        self.changelist = changelist
        self.resource = resource
        self.filters = list()
    
    def register_filter(self, a_filter, **kwargs):
        kwargs['section'] = self
        self.filters.append(a_filter(**kwargs))
    
    def make_link(self, **kwargs):
        return self.changelist.make_link(**kwargs)
    
    def populate_state(self, state):
        for a_filter in self.filters:
            a_filter.populate_state(state)
    
    def get_links(self, state, **link_kwargs):
        links = list()
        for a_filter in self.filters:
            links.extend(a_filter.get_links(state, **link_kwargs))
        return links
    
    def filter_index(self, state, active_index):
        for a_filter in self.filters:
            if a_filter.is_active(state):
                new_index = a_filter.filter_index(state, active_index)
                if new_index is not None:
                    active_index = new_index
        return active_index

