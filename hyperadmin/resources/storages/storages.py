import os

from hyperadmin.hyperobjects import Link
from hyperadmin.resources.crud.crud import CRUDResource
from hyperadmin.resources.storages import views
from hyperadmin.resources.storages.forms import UploadForm, UploadLinkForm
from hyperadmin.resources.storages.changelist import StorageChangeList, StoragePaginator
from hyperadmin.resources.storages.endpoints import ListEndpoint, CreateEndpoint, CreateUploadEndpoint, DetailEndpoint, DeleteEndpoint


class StorageResource(CRUDResource):
    #resource_adaptor = storage object
    changelist_class = StorageChangeList
    paginator_class = StoragePaginator
    form_class = UploadForm
    upload_link_form_class = UploadLinkForm
    
    list_view = views.StorageListView
    add_view = views.StorageCreateView
    upload_link_view = views.StorageUploadLinkView
    detail_view = views.StorageDetailView
    delete_view = views.StorageDeleteView
    
    def __init__(self, **kwargs):
        self._app_name = kwargs.pop('app_name', '-storages')
        self._resource_name = kwargs.pop('resource_name')
        super(StorageResource, self).__init__(**kwargs)
    
    def get_app_name(self):
        return self._app_name
    app_name = property(get_app_name)
    
    def get_resource_name(self):
        return self._resource_name
    resource_name = property(get_resource_name)
    
    def get_storage(self):
        return self.resource_adaptor
    storage = property(get_storage)
    
    def get_upload_link_form_class(self):
        return self.upload_link_form_class
    
    def get_view_endpoints(self):
        endpoints = super(CRUDResource, self).get_view_endpoints()
        endpoints.extend([
            ListEndpoint(resource=self),
            CreateEndpoint(resource=self),
            CreateUploadEndpoint(resource=self),
            DetailEndpoint(resource=self),
            DeleteEndpoint(resource=self),
        ])
        return endpoints
    
    def get_listing(self, path):
        try:
            dirs, files = self.resource_adaptor.listdir(path)
            if path:
                files = [os.path.join(path, filename) for filename in files]
            return dirs, files
        except NotImplementedError:
            return [], [] #dirs, files
    
    def get_primary_query(self):
        path = self.state.params.get('path', '')
        return self.get_listing(path)
    
    def get_instances(self):
        '''
        Returns a set of native objects for a given state
        '''
        if 'page' in self.state:
            return self.state['page'].object_list
        if self.state.has_view_class('change_form'):
            return []
        dirs, files = self.get_primary_query()
        instances = [views.BoundFile(self.storage, file_name) for file_name in files]
        return instances
    
    def get_index_queries(self):
        links = self.create_link_collection()
        if 'filter_links' in self.state:
            links += self.state['filter_links']
        return links
    
    def get_form_kwargs(self, item=None, **kwargs):
        kwargs = super(StorageResource, self).get_form_kwargs(item, **kwargs)
        kwargs['storage'] = self.storage
        return kwargs
    
    def get_upload_link_form_kwargs(self, **kwargs):
        kwargs = self.get_form_kwargs(**kwargs)
        kwargs['resource'] = self
        return kwargs
    
    def get_item_url(self, item):
        return self.link_prototypes['update'].get_url(item=item)
    
    def get_item_storage_link(self, item, **kwargs):
        link_kwargs = {'url':item.instance.url,
                       'resource':self,
                       'prompt':'Absolute Url',
                       'rel':'storage-url',}
        link_kwargs.update(kwargs)
        storage_link = Link(**link_kwargs)
        return storage_link
    
    def get_item_outbound_links(self, item):
        links = self.create_link_collection()
        links.append(self.get_item_storage_link(item, link_factor='LO'))
        return links
    
    def get_item_prompt(self, item):
        return item.instance.name
    
    def get_paginator_kwargs(self):
        return {'storage':self.storage,
                'state':self.state,}
