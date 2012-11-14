from hyperadmin.resources.endpoints import EndpointLink, Endpoint
from hyperadmin.resources.crud.endpoints import ListEndpoint as BaseListEndpoint, CreateEndpoint, DetailEndpoint as BaseDetailEndpoint, DeleteEndpoint as BaseDeleteEndpoint


class CreateUploadEndpointLink(EndpointLink):
    def show_link(self, **kwargs):
        return self.resource.has_add_permission()
    
    def get_link_kwargs(self, **kwargs):
        form_kwargs = kwargs.pop('form_kwargs', None)
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.resource.get_upload_link_form_kwargs(**form_kwargs)
        
        link_kwargs = {'url':self.get_url(),
                       'resource':self,
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_kwargs':form_kwargs,
                       'form_class': self.resource.get_upload_link_form_class(),
                       'prompt':'create upload link',
                       'rel':'upload-link',}
        link_kwargs.update(kwargs)
        return super(CreateUploadEndpointLink, self).get_link_kwargs(**link_kwargs)
    
    def on_success(self, link):
        return link

class ListEndpoint(BaseListEndpoint):
    def get_outbound_links(self):
        links = super(ListEndpoint, self).get_outbound_links()
        links.add_link('upload', link_factor='LO')
        return links

class CreateUploadEndpoint(Endpoint):
    name_suffix = 'upload'
    url_suffix = r'^upload/$'
    
    def get_view_class(self):
        return self.resource.upload_link_view
    
    def get_links(self):
        return {'upload':CreateUploadEndpointLink(endpoint=self)}

class DetailEndpoint(BaseDetailEndpoint):
    url_suffix = r'^(?P<path>.+)/$'
    
    def get_url(self, item):
        return super(BaseDetailEndpoint, self).get_url(path=item.instance.name)

class DeleteEndpoint(BaseDeleteEndpoint):
    url_suffix = r'^(?P<path>.+)/delete/$'
    
    def get_url(self, item):
        return super(BaseDeleteEndpoint, self).get_url(path=item.instance.name)

