from hyperadmin.resources.endpoints import LinkPrototype, Endpoint


class ListLinkPrototype(LinkPrototype):
    def get_link_kwargs(self, **kwargs):
        link_kwargs = {'url':self.get_url(),
                       'resource':self,
                       'prompt':'list',
                       'rel':'list',}
        link_kwargs.update(kwargs)
        return super(ListLinkPrototype, self).get_link_kwargs(**link_kwargs)


class ListEndpoint(Endpoint):
    name_suffix = 'list'
    url_suffix = r'^$'
    
    def get_view_class(self):
        return self.resource.list_view
    
    def get_links(self):
        return {'list':ListLinkPrototype(endpoint=self),}

