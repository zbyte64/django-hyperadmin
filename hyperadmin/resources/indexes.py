class Index(object):
    paginator_class = None
    
    def __init__(self, name, resource, query):
        self.name = name
        self.resource = resource
        self.state = self.resource.state
        self.filters = list()
        self.query = query
    
    def register_filter(self, a_filter, **kwargs):
        kwargs['index'] = self
        self.filters.append(a_filter(**kwargs))
    
    def populate_state(self):
        for a_filter in self.filters:
            a_filter.populate_state()
    
    def get_index_query(self):
        return self.query
    
    def get_filtered_index(self):
        active_index = self.get_index_query()
        for a_filter in self.filters:
            if a_filter.is_active():
                new_index = a_filter.filter_index(active_index)
                if new_index is not None:
                    active_index = new_index
        return active_index
    
    def make_link(self, **kwargs):
        return self.resource.get_resource_link(**kwargs)
    
    def get_filter_links(self, **link_kwargs):
        links = list()
        for a_filter in self.filters:
            links.extend(a_filter.get_links(**link_kwargs))
        return links
    
    def get_paginator_kwargs(self):
        return {}
    
    def get_paginator(self, **kwargs):
        index = self.get_filtered_index()
        kwargs.update(self.get_paginator_kwargs())
        if self.paginator_class:
            return self.paginator_class(index, **kwargs)
        return self.resource.get_paginator(index, **kwargs)
    
    def get_advaned_link(self):
        """
        Return a link with all the options in one form, ignores pagination
        """
        pass

class PrimaryIndex(Index):
    pass

