from django.utils.translation import ugettext as _
from django.views import generic

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

class StorageResourceViewMixin(CRUDResourceViewMixin, generic.edit.FormMixin):
    def get_links_and_items(self):
        if not hasattr(self, '_links'):
            self._links, self._items = self.resource.get_links_and_items(self.request)
        return self._links, self._items
    
    def get_items(self, **kwargs):
        return self.get_links_and_items()[1]
    
    def get_items_forms(self, **kwargs):
        return [self.get_form(**self.get_form_kwargs(instance=item)) for item in self.get_items()]
    
    def get_form_kwargs(self, **defaults):
        kwargs = dict(defaults)
        kwargs.update(CRUDResourceViewMixin.get_form_kwargs(self))
        kwargs['storage'] = self.resource.resource_adaptor
        return kwargs

class StorageListResourceView(StorageResourceViewMixin, generic.View): #generic.UpdateView
    view_class = 'change_list'
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_list_link())
    
    def post(self, request, *args, **kwargs):
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_create_link(**form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)
    
    def get_ln_links(self, instance=None):
        update_link = self.get_upload_link(instance=instance)
        return [update_link] + super(StorageListResourceView, self).get_ln_links(instance)
    
    def get_templated_queries(self):
        links = super(StorageListResourceView, self).get_templated_queries()
        links += self.get_links_and_items()[0]
        return links

#TODO
StorageAddResourceView = StorageListResourceView

class StorageDetailResourceView(StorageResourceViewMixin, generic.View): #generic.ListView
    view_class = 'change_form'
    
    def get_object(self):
        return BoundFile(self.resource.resource_adaptor, self.kwargs['path'])
    
    def get_items(self, **kwargs):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return [self.object]
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_update_link(instance=self.object))
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_update_link(instance=self.object, **form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete():
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_delete_link(instance=self.object, **form_kwargs)
        response_link = form_link.submit()
        
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)

StorageDeleteResourceView = StorageDetailResourceView

