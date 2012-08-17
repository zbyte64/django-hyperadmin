from django.utils.translation import ugettext as _
from django.views import generic
from django import http

from hyperadmin.models import log_action, DELETION
from hyperadmin.resources.links import Link

from common import ResourceViewMixin

class BoundFile(object):
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name
    
    @property
    def url(self):
        return self.storage.url(self.name)
    
    def delete(self):
        return self.storage.delete(self.name)

class StorageResourceViewMixin(ResourceViewMixin, generic.edit.FormMixin):
    def get_links_and_items(self):
        if not hasattr(self, '_links'):
            self._links, self._items = self.resource.get_links_and_items(self.request)
        return self._links, self._items
    
    def get_items(self, **kwargs):
        return self.get_links_and_items()[1]
    
    def get_items_forms(self, **kwargs):
        return [self.get_form(instance=item) for item in self.get_items()]
    
    def get_form_class(self, instance=None):
        return self.resource.get_form_class()
    
    def get_form(self, **kwargs):
        form_class = self.get_form_class()
        form = form_class(**kwargs)
        return form
    
    def get_upload_link(self, instance=None):
        if hasattr(self.resource.resource_adaptor, 'get_upload_link'):
            return self.resource.resource_adaptor.get_upload_link(instance=instance)
        else:
            kwargs = self.get_form_kwargs()
            kwargs['instance'] = instance
            form = self.get_form(**kwargs)
            link_params = {'url':self.request.path,
                           'method':'POST',
                           'form':form,}
            if instance:
                link_params['prompt'] = 'update'
                link_params['rel'] = 'update'
            else:
                link_params['prompt'] = 'create'
                link_params['rel'] = 'create'
            return Link(**link_params)

class StorageListResourceView(StorageResourceViewMixin, generic.View): #generic.UpdateView
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self)
    
    def post(self, request, *args, **kwargs):
        return self.resource.generate_create_response(self, form_class=self.get_form_class())
    
    def get_ln_links(self, instance=None):
        form = self.get_form(instance=instance)
        update_link = self.get_upload_link(instance=instance)
        return [update_link] + super(StorageListResourceView, self).get_ln_links(instance)
    
    def get_templated_queries(self):
        links = super(StorageListResourceView, self).get_templated_queries()
        links += self.get_links_and_items()[0]
        return links

class StorageDetailResourceView(StorageResourceViewMixin, generic.View): #generic.ListView
    #TODO get_form retrieves information from mediatype
    
    def get_object(self):
        return BoundFile(self.resource.resource_adaptor, self.kwargs['path'])
    
    def get_items(self, **kwargs):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return [self.object]
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_response(self, instance=self.object)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_update_response(self, instance=self.object, form_class=self.get_form_class())
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        #if not self.can_delete():
        #    return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        #with log_action(request.user, self.object, DELETION, request=request):
        self.object.delete()
        
        return self.resource.generate_delete_response(self)
    
    def get_ln_links(self, instance=None):
        links = super(StorageDetailResourceView, self).get_ln_links(instance)
        assert instance
        if instance:
            update_link = self.get_upload_link(instance=instance)
            return [update_link] + links
        return links

