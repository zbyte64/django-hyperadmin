from django.utils.datastructures import SortedDict

class ChangeList(object):
    ordering = None
    paginator_class = None #default to resource.get_paginator
    page_var = 'p'
    
    def __init__(self, resource, state):
        self.resource = resource
        self.sections = SortedDict()
        self.state = state
    
    def detect_sections(self):
        for key, index in self.resource.get_indexes().iteritems():
            section = FilterSection(name=key, changelist=self, resource=self.resource, index=index)
            self.sections[key] = section
    
    def get_active_section(self):
        return None
    
    def populate_state(self):
        for section in self.sections.itervalues():
            section.populate_state()
        active_section = self.get_active_section()
        if active_section:
            state = self.state
            state['paginator'] = active_section.get_paginator()
            page_num = int(self.state.params.get(self.page_var, 1))
            state['page'] = state['paginator'].page(page_num)
    
    def make_link(self, **kwargs):
        return self.resource.get_resource_link(**kwargs)
    
    def get_links(self):
        links = list()
        for section in self.sections.itervalues():
            links.extend(section.get_filter_links(rel=section.name))
        active_section = self.get_active_section()
        if active_section:
            links += active_section.get_pagination_links()
        return links
    
    def get_paginator_kwargs(self):
        return {}
    
    def get_ordering(self):
        if self.ordering is not None:
            return self.ordering
        return self.resurce.get_ordering()


class FilterSection(object):
    def __init__(self, name, changelist, resource, index):
        self.name = name
        self.changelist = changelist
        self.resource = resource
        self.index = index
        self.state = resource.state
    
    def make_link(self, **kwargs):
        return self.changelist.make_link(**kwargs)
    
    def populate_state(self):
        self.index.populate_state()
    
    def get_filtered_index(self):
        return self.index.get_filtered_index()
    
    def get_filter_links(self, **link_kwargs):
        return self.index.get_filter_links(**link_kwargs)
    
    def get_paginator(self, **kwargs):
        params = self.changelist.get_paginator_kwargs()
        params.update(kwargs)
        return self.index.get_paginator(**params)
    
    def get_pagination_links(self):
        links = list()
        if 'paginator' in self.state:
            paginator = self.state['paginator']
            classes = ["pagination"]
            for page in range(paginator.num_pages):
                if page == '.':
                    continue
                url = self.state.get_query_string({self.changelist.page_var: page+1})
                links.append(self.make_link(url=url, prompt=u"%s" % page, classes=classes, rel="pagination"))
        return links

