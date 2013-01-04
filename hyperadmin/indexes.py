class Index(object):
    paginator_class = None
    page_var = 'p'
    
    def __init__(self, name, resource, query):
        self.name = name
        self.resource = resource
        self.filters = list()
        self.query = query
    
    @property
    def state(self):
        return self.resource.state
    
    def register_filter(self, a_filter, **kwargs):
        kwargs['index'] = self
        self.filters.append(a_filter(**kwargs))
    
    def populate_state(self):
        for a_filter in self.filters:
            a_filter.populate_state()
    
    def get_index_query(self):
        return self.query
    
    def get(self, **kwargs):
        return self.get_index_query().get(**kwargs)
    
    def get_resource_item(self, **kwargs):
        return self.resource.get_resource_item(self.get(**kwargs))
    
    def get_filtered_index(self):
        active_index = self.get_index_query()
        for a_filter in self.filters:
            if a_filter.is_active():
                new_index = a_filter.filter_index(active_index)
                if new_index is not None:
                    active_index = new_index
        return active_index
    
    def get_link(self, **kwargs):
        return self.resource.get_link(**kwargs)
    
    def get_filter_links(self, **link_kwargs):
        links = list()
        for a_filter in self.filters:
            links.extend(a_filter.get_links(**link_kwargs))
        return links
    
    def get_paginator_kwargs(self):
        return self.resource.get_paginator_kwargs()
    
    def get_paginator(self, **kwargs):
        index = self.get_filtered_index()
        kwargs.update(self.get_paginator_kwargs())
        if self.paginator_class:
            return self.paginator_class(index, **kwargs)
        return self.resource.get_paginator(index, **kwargs)
    
    def get_pagination_links(self, **link_kwargs):
        links = list()
        if 'paginator' in self.state:
            paginator = self.state['paginator']
            classes = ["pagination"]
            for page in range(paginator.num_pages):
                if page == '.':
                    continue
                url = self.state.get_query_string({self.page_var: page+1})
                kwargs = {
                    'url':url,
                    'prompt': u"%s" % page,
                    'classes': classes,
                    'rel': "pagination",
                }
                kwargs.update(link_kwargs)
                links.append(self.get_link(**kwargs))
        return links
    
    def get_advaned_link(self):
        """
        Return a link with all the options in one form, ignores pagination
        """
        pass
    
    def get_links(self, **kwargs):
        links = self.get_filter_links(**kwargs)
        #active_section = self.get_active_section()
        #if active_section:
        #    links += active_section.get_pagination_links()
        return links
    
    def get_page(self):
        paginator = self.get_paginator()
        return paginator.page(self.state.params.get(self.page_var, 1))

class PrimaryIndex(Index):
    def get_paginator_kwargs(self):
        return self.resource.get_paginator_kwargs()
