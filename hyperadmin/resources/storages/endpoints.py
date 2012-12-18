from hyperadmin.resources.endpoints import LinkPrototype, Endpoint
from hyperadmin.resources.crud.endpoints import ListEndpoint as BaseListEndpoint, CreateEndpoint, DetailEndpoint as BaseDetailEndpoint, DeleteEndpoint as BaseDeleteEndpoint
from hyperadmin.resources.storages.views import BoundFile


class CreateUploadLinkPrototype(LinkPrototype):
    def show_link(self, **kwargs):
        return self.resource.has_add_permission()
    
    def get_link_kwargs(self, **kwargs):
        form_kwargs = kwargs.pop('form_kwargs', None)
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.resource.get_upload_link_form_kwargs(**form_kwargs)
        
        link_kwargs = {'url':self.get_url(),
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_kwargs':form_kwargs,
                       'form_class': self.resource.get_upload_link_form_class(),
                       'prompt':'create upload link',
                       'rel':'upload-link',}
        link_kwargs.update(kwargs)
        return super(CreateUploadLinkPrototype, self).get_link_kwargs(**link_kwargs)
    
    def on_success(self, link):
        return link

class ListEndpoint(BaseListEndpoint):
    def get_outbound_links(self):
        links = self.create_link_collection()
        links.add_link('upload', link_factor='LO')
        return links

class CreateUploadEndpoint(Endpoint):
    name_suffix = 'upload'
    url_suffix = r'^upload/$'
    
    def get_link_prototypes(self):
        return {'GET':CreateUploadLinkPrototype(endpoint=self, name='upload'),
                'POST':CreateUploadLinkPrototype(endpoint=self, name='upload')}

class DetailMixin(object):
    def get_object(self):
        if not hasattr(self, 'object'):
            self.object = BoundFile(self.resource.resource_adaptor, self.kwargs['path'])
            if not self.object.exists():
                raise http.Http404
        return self.object

class DetailEndpoint(DetailMixin, BaseDetailEndpoint):
    url_suffix = r'^(?P<path>.+)/$'
    
    def get_url(self, item):
        return super(BaseDetailEndpoint, self).get_url(path=item.instance.name)

class DeleteEndpoint(DetailMixin, BaseDeleteEndpoint):
    url_suffix = r'^(?P<path>.+)/delete/$'
    
    def get_url(self, item):
        return super(BaseDeleteEndpoint, self).get_url(path=item.instance.name)

