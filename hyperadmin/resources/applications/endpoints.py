from hyperadmin.links import LinkPrototype
from hyperadmin.resources.endpoints import ResourceEndpoint


class ListLinkPrototype(LinkPrototype):
    def get_link_kwargs(self, **kwargs):
        link_kwargs = {'url':self.get_url(),
                       'resource':self,
                       'prompt':'list',
                       'rel':'list',}
        link_kwargs.update(kwargs)
        return super(ListLinkPrototype, self).get_link_kwargs(**link_kwargs)


class ListEndpoint(ResourceEndpoint):
    endpoint_class = 'index'
    view_class = 'app_index'
    
    prototype_method_map = {
        'GET': 'list',
    }
    
    name_suffix = 'list'
    url_suffix = r'^$'
    
    list_prototype = ListLinkPrototype
    
    def get_link_prototypes(self):
        return [
            (self.list_prototype, {'name':'list'}),
        ]

