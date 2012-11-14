from hyperadmin.hyperobjects import Link
from hyperadmin.resources.endpoints import EndpointLink, Endpoint


class ListEndpointLink(EndpointLink):
    def get_link(self, **link_kwargs):
        link_kwargs = {'url':self.get_url(),
                       'resource':self,
                       'prompt':'list',
                       'rel':'list',}
        link_kwargs.update(link_kwargs)
        create_link = Link(**link_kwargs)
        return create_link

class ListEndpoint(Endpoint):
    name_suffix = 'list'
    url_suffix = r'^$'
    
    def get_view_class(self):
        return self.resource.list_view
    
    def get_links(self):
        #TODO add restful create
        return {'list':ListEndpointLink(endpoint=self)}

class CreateEndpointLink(EndpointLink):
    def show_link(self):
        return True
        return self.resource.has_add_permission()
    
    def get_link(self, **link_kwargs):
        form_kwargs = link_kwargs.pop('form_kwargs', None)
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
        link_kwargs.update(link_kwargs)
        create_link = Link(**link_kwargs)
        return create_link
    
    def handle_submission(self, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            resource_item = self.resource.get_resource_item(instance)
            return self.on_success(resource_item)
        return link.clone(form=form)
    
    def on_success(self, item):
        return item.get_item_link()

class CreateEndpoint(Endpoint):
    name_suffix = 'add'
    url_suffix = r'^add/$'
    
    def get_view_class(self):
        return self.resource.add_view
    
    def get_links(self):
        return {'create':CreateEndpointLink(endpoint=self)}

class UpdateEndpointLink(EndpointLink):
    def show_link(self):
        return True
        return not self.state.has_view_class('delete_confirmation')
        return self.resource.has_add_permission()
    
    def get_link(self, item, **link_kwargs):
        form_kwargs = link_kwargs.pop('form_kwargs', None)
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.resource.get_form_kwargs(item, **form_kwargs)
        
        link_kwargs = {'url':self.get_url(item),
                       'resource':self,
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_kwargs':form_kwargs,
                       'form_class': item.get_form_class(),
                       'prompt':'update',
                       'rel':'update',}
        link_kwargs.update(link_kwargs)
        create_link = Link(**link_kwargs)
        return create_link
    
    def handle_submission(self, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            resource_item = self.resource.get_resource_item(instance)
            return self.on_success(resource_item)
        return link.clone(form=form)
    
    def on_success(self, item):
        return item.get_item_link()
    
    def get_url(self, item):
        return super(UpdateEndpointLink, self).get_url(pk=item.instance.pk)

class DetailEndpoint(Endpoint):
    name_suffix = 'detail'
    url_suffix = r'^(?P<pk>\w+)/$'
    
    def get_view_class(self):
        return self.resource.detail_view
    
    def get_links(self):
        #TODO add restful delete
        return {'update':UpdateEndpointLink(endpoint=self)}

class DeleteEndpointLink(EndpointLink):
    def show_link(self):
        return True
        return self.resource.has_delete_permission()
    
    def get_link(self, item, **link_kwargs):
        link_kwargs = {'url':self.get_url(item),
                       'resource':self,
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'prompt':'delete',
                       'rel':'delete',}
        link_kwargs.update(link_kwargs)
        create_link = Link(**link_kwargs)
        return create_link
    
    def handle_submission(self, link, submit_kwargs):
        instance = self.resource.state.item.instance
        instance.delete()
        return self.on_success()
    
    def get_url(self, item):
        return super(UpdateEndpointLink, self).get_url(pk=item.instance.pk)

class DeleteEndpoint(Endpoint):
    name_suffix = 'delete'
    url_suffix = r'^(?P<pk>\w+)/delete/$'
    
    def get_view_class(self):
        return self.resource.delete_view
    
    def get_links(self):
        return {'delete':DeleteEndpointLink(endpoint=self)}

