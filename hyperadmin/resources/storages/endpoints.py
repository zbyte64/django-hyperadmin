from hyperadmin.endpoints import LinkPrototype, Endpoint
from hyperadmin.resources.crud.endpoints import ListEndpoint as BaseListEndpoint, CreateEndpoint, DetailEndpoint as BaseDetailEndpoint, DeleteEndpoint as BaseDeleteEndpoint


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
        links = self.create_link_collection()
        links.add_link('upload', link_factor='LO')
        return links

class CreateUploadEndpoint(Endpoint):
    name_suffix = 'upload'
    url_suffix = r'^upload/$'
    
    create_upload_prototype = CreateUploadLinkPrototype
    
    def get_link_prototypes(self):
        return [
            (self.create_upload_prototype, {'name':'upload'}),
        ]
    
    def get_link_prototypes_per_method(self):
        return {'GET': self.link_prototypes['upload'],
                'POST': self.link_prototypes['upload'],}

class DetailEndpoint(BaseDetailEndpoint):
    url_suffix = r'^(?P<path>.+)/$'
    
    def get_url(self, item):
        return super(BaseDetailEndpoint, self).get_url(path=item.instance.name)

class DeleteEndpoint(BaseDeleteEndpoint):
    url_suffix = r'^(?P<path>.+)/delete/$'
    
    def get_url(self, item):
        return super(BaseDeleteEndpoint, self).get_url(path=item.instance.name)

