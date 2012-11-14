from hyperadmin.resources.endpoints import EndpointLink, Endpoint
from hyperadmin.resources.crud.endpoints import ListEndpoint, CreateEndpoint, DetailEndpoint, DeleteEndpoint

class InlineListEndpoint(ListEndpoint):
    def get_url(self):
        pk = self.state['parent'].pk
        return super(InlineListEndpoint, self).get_url(pk=pk)

class InlineCreateEndpoint(DetailEndpoint):
    def get_url(self):
        pk = self.state['parent'].pk
        return super(InlineCreateEndpoint, self).get_url(pk=pk)

class InlineDetailEndpoint(DetailEndpoint):
    url_suffix = r'^(?P<inline_pk>\w+)/$'
    
    def get_url(self, item):
        pk = self.state['parent'].pk
        return super(InlineDetailEndpoint, self).get_url(pk=pk, inline_pk=item.instance.pk)

class InlineDeleteEndpoint(DeleteEndpoint):
    url_suffix = r'^(?P<inline_pk>\w+)/delete/$'
    
    def get_url(self, item):
        pk = self.state['parent'].pk
        return super(InlineDeleteEndpoint, self).get_url(pk=pk, inline_pk=item.instance.pk)

