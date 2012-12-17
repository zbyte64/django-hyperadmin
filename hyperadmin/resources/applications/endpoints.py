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
    endpoint_class = 'index'
    view_class = 'app_index'
    
    name_suffix = 'list'
    url_suffix = r'^$'
    
    def get_link_prototypes(self):
        return {'GET':ListLinkPrototype(endpoint=self, name='list'),}
