from django.utils.translation import ugettext as _
from django.views.generic import View

from hyperadmin.hyperobjects import Link
from hyperadmin.resources.views import CRUDResourceViewMixin

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

class StorageResourceViewMixin(CRUDResourceViewMixin):
    def get_links_and_items(self):
        if not hasattr(self, '_links'):
            self._links, self._items = self.resource.get_links_and_items(self.request)
        return self._links, self._items

class StorageListResourceView(StorageResourceViewMixin, View):
    view_class = 'change_list'
    
    def get_state(self):
        state = super(StorageListResourceView, self).get_state()
        links, items = self.get_links_and_items()
        state['links'] = links
        state['items'] = items
        return state
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_list_link(), self.state)
    
    def post(self, request, *args, **kwargs):
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_restful_create_link(**form_kwargs)
        response_link = form_link.submit(self.state)
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, self.state)

class StorageAddResourceView(StorageResourceViewMixin, View):
    view_class = 'change_list'
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_create_link(), self.state)
    
    def post(self, request, *args, **kwargs):
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_create_link(**form_kwargs)
        response_link = form_link.submit(self.state)
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, self.state)

class StorageDetailResourceView(StorageResourceViewMixin, View):
    view_class = 'change_form'
    
    def get_state(self):
        state = super(StorageDetailResourceView, self).get_state()
        state.item = self.get_item()
        return state
    
    def get_object(self):
        return BoundFile(self.resource.resource_adaptor, self.kwargs['path'])
    
    def get_item(self):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return self.resource.get_resource_item(self.object)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        item = self.get_item()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_update_link(item), self.state)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        item = self.get_item()
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_update_link(item, **form_kwargs)
        response_link = form_link.submit(self.state)
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, self.state)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete():
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        item = self.get_item()
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_restful_delete_link(item, **form_kwargs)
        response_link = form_link.submit(self.state)
        
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, self.state)

class StorageDeleteResourceView(StorageResourceViewMixin, View):
    view_class = 'delete_confirmation'
    
    def get_state(self):
        state = super(StorageDetailResourceView, self).get_state()
        state.item = self.get_item()
        return state
    
    def get_object(self):
        return BoundFile(self.resource.resource_adaptor, self.kwargs['path'])
    
    def get_item(self):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return self.resource.get_resource_item(self.object)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        item = self.get_item()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_delete_link(item), self.state)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete():
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        item = self.get_item()
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_delete_link(item, **form_kwargs)
        response_link = form_link.submit(self.state)
        
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, self.state)

