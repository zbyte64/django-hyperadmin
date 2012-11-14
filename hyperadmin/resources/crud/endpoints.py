from hyperadmin.resources.endpoints import EndpointLink, Endpoint


class ListEndpointLink(EndpointLink):
    def get_link_kwargs(self, **kwargs):
        link_kwargs = {'url':self.get_url(),
                       'resource':self,
                       'prompt':'list',
                       'rel':'list',}
        link_kwargs.update(kwargs)
        return super(ListEndpointLink, self).get_link_kwargs(**link_kwargs)

class CreateEndpointLink(EndpointLink):
    def show_link(self):
        return True
        return self.resource.has_add_permission()
    
    def get_link_kwargs(self, **kwargs):
        form_kwargs = kwargs.pop('form_kwargs', None)
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.resource.get_form_kwargs(**form_kwargs)
        
        link_kwargs = {'url':self.get_url(),
                       'resource':self,
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_kwargs':form_kwargs,
                       'form_class': self.resource.get_form_class(),
                       'prompt':'create',
                       'rel':'create',}
        link_kwargs.update(kwargs)
        return super(CreateEndpointLink, self).get_link_kwargs(**link_kwargs)

class UpdateEndpointLink(EndpointLink):
    def show_link(self):
        return True
        return not self.state.has_view_class('delete_confirmation')
        return self.resource.has_add_permission()
    
    def get_link_kwargs(self, **kwargs):
        item = kwargs.pop('item')
        form_kwargs = kwargs.pop('form_kwargs', None)
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.resource.get_form_kwargs(item, **form_kwargs)
        
        link_kwargs = {'url':self.get_url(item=item),
                       'resource':self,
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_kwargs':form_kwargs,
                       'form_class': item.get_form_class(),
                       'prompt':'update',
                       'rel':'update',}
        link_kwargs.update(kwargs)
        return super(UpdateEndpointLink, self).get_link_kwargs(**link_kwargs)

class DeleteEndpointLink(EndpointLink):
    def show_link(self):
        return True
        return self.resource.has_delete_permission()
    
    def get_link_kwargs(self, **kwargs):
        item = kwargs.pop('item')
        link_kwargs = {'url':self.get_url(item=item),
                       'resource':self,
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'prompt':'delete',
                       'rel':'delete',}
        link_kwargs.update(kwargs)
        return super(DeleteEndpointLink, self).get_link_kwargs(**link_kwargs)
    
    def handle_submission(self, link, submit_kwargs):
        instance = self.resource.state.item.instance
        instance.delete()
        return self.on_success()

class ListEndpoint(Endpoint):
    name_suffix = 'list'
    url_suffix = r'^$'
    
    def get_view_class(self):
        return self.resource.list_view
    
    def get_links(self):
        return {'list':ListEndpointLink(endpoint=self),
                'rest-create':CreateEndpointLink(endpoint=self),}
    
    def get_outbound_links(self):
        links = super(ListEndpoint, self).get_outbound_links()
        if 'create' in self.resource.links and self.resource.links['create'].show_link():
            links.append(self.resource.links['create'].get_link(link_factor='LO'))
        return links

class CreateEndpoint(Endpoint):
    name_suffix = 'add'
    url_suffix = r'^add/$'
    
    def get_view_class(self):
        return self.resource.add_view
    
    def get_links(self):
        return {'create':CreateEndpointLink(endpoint=self)}

class DetailEndpoint(Endpoint):
    name_suffix = 'detail'
    url_suffix = r'^(?P<pk>\w+)/$'
    
    def get_view_class(self):
        return self.resource.detail_view
    
    def get_links(self):
        return {'update':UpdateEndpointLink(endpoint=self),
                'rest-update':UpdateEndpointLink(endpoint=self, link_kwargs={'method':'PUT'}),
                'rest-delete':DeleteEndpointLink(endpoint=self, link_kwargs={'method':'DELETE'}),}
    
    def get_item_outbound_links(self, item):
        links = super(DetailEndpoint, self).get_item_outbound_links(item)
        #TODO maybe something like:
        #self.resources.add_link_if_active(links, 'delete', link_factor='LO')
        if self.resource.links['delete'].show_link():
            links.append(self.resource.links['delete'].get_link(link_factor='LO'))
        return links
    
    def get_url(self, item):
        print 'detail get url:', item
        return super(DetailEndpoint, self).get_url(pk=item.instance.pk)

class DeleteEndpoint(Endpoint):
    name_suffix = 'delete'
    url_suffix = r'^(?P<pk>\w+)/delete/$'
    
    def get_view_class(self):
        return self.resource.delete_view
    
    def get_links(self):
        return {'delete':DeleteEndpointLink(endpoint=self)}
    
    def get_url(self, item):
        return super(DeleteEndpoint, self).get_url(pk=item.instance.pk)

