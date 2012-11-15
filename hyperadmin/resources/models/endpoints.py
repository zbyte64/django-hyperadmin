from hyperadmin.resources.crud.endpoints import ListEndpoint, CreateEndpoint, DetailEndpoint, DeleteEndpoint

class InlineListEndpoint(ListEndpoint):
    def get_url(self):
        pk = self.state['parent'].pk
        return super(ListEndpoint, self).get_url(pk=pk)

class InlineCreateEndpoint(DetailEndpoint):
    def get_url(self):
        pk = self.state['parent'].pk
        return super(CreateEndpoint, self).get_url(pk=pk)

class InlineDetailEndpoint(DetailEndpoint):
    url_suffix = r'^(?P<inline_pk>\w+)/$'
    
    def get_url(self, item):
        pk = self.state['parent'].pk
        return super(DetailEndpoint, self).get_url(pk=pk, inline_pk=item.instance.pk)

class InlineDeleteEndpoint(DeleteEndpoint):
    url_suffix = r'^(?P<inline_pk>\w+)/delete/$'
    
    def get_url(self, item):
        pk = self.state['parent'].pk
        return super(DeleteEndpoint, self).get_url(pk=pk, inline_pk=item.instance.pk)

