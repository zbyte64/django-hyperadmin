from hyperadmin.links import LinkPrototype
from hyperadmin.resources.endpoints import ResourceEndpoint
from hyperadmin.resources.crud.endpoints import ListEndpoint as BaseListEndpoint, CreateEndpoint, DetailEndpoint, DeleteEndpoint


class BoundFile(object):
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name
    
    @property
    def pk(self):
        return self.name
    
    @property
    def url(self):
        return self.storage.url(self.name)
    
    def delete(self):
        return self.storage.delete(self.name)
    
    def exists(self):
        return self.storage.exists(self.name)
    
    def __unicode__(self):
        return self.name

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
        #links = self.create_link_collection()
        links = super(ListEndpoint, self).get_outbound_links()
        links.add_link('upload', link_factor='LO')
        return links

class CreateUploadEndpoint(ResourceEndpoint):
    name_suffix = 'upload'
    url_suffix = r'^upload/$'
    
    prototype_method_map = {
        'GET': 'upload',
        'POST': 'upload',
    }
    
    create_upload_prototype = CreateUploadLinkPrototype
    
    def get_link_prototypes(self):
        return [
            (self.create_upload_prototype, {'name':'upload'}),
        ]

