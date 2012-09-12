from django import http

import mimeparse

class ConditionalAccessMixin(object):
    etag_function = None
    
    def check_etag(self, data):
        new_etag = self.etag_function and self.etag_function(data)
        if not new_etag:
            return
        if self.request.META.get('HTTP_IF_NONE_MATCH', None) == new_etag:
            raise http.HttpResponseNotModified()
        if self.request.META.get('HTTP_IF_MATCH', new_etag) != new_etag:
            raise http.HttpResponse(status=412) # Precondition Failed
        
    # def dispatch(self, request, *args, **kwargs):
    #     return super(ConditionalAccessMixin, self).dispatch(request, *args, **kwargs)

class ResourceViewMixin(ConditionalAccessMixin):
    resource = None
    resource_site = None
    view_class = None
    
    def get_response_type(self):
        return mimeparse.best_match(
            self.resource_site.media_types.keys(), 
            self.request.META.get('HTTP_ACCEPT', '')
        )
    
    def get_request_type(self):
        return mimeparse.best_match(
            self.resource_site.media_types.keys(), 
            self.request.META.get('CONTENT_TYPE', self.request.META.get('HTTP_ACCEPT', ''))
        )
    
    def get_response_media_type(self):
        return self.resource.get_response_media_type(self)
    
    def get_request_media_type(self):
        return self.resource.get_request_media_type(self)
    
    def get_request_form_kwargs(self):
        media_type = self.get_request_media_type()
        form_kwargs = media_type.deserialize()
        return form_kwargs
    
    def get_embedded_links(self, instance=None):
        return self.resource.get_embedded_links(instance)
    
    def get_outbound_links(self, instance=None):
        return self.resource.get_outbound_links(instance)
    
    def get_templated_queries(self):
        return self.resource.get_templated_queries()
    
    #TODO find a better name
    def get_ln_links(self, instance=None):
        return self.resource.get_ln_links(instance)
    
    #TODO find a better name
    def get_li_links(self, instance=None):
        return self.resource.get_li_links(instance)
    
    def get_instance_url(self, instance):
        return self.resource.get_instance_url(instance)
    
    def get_items(self):
        return []
    
    def get_resource_items(self):
        return [self.resource.get_resource_item(item) for item in self.get_items()]
    
    def get_form_class(self, instance=None):
        return None
    
    def get_form_kwargs(self):
        return {}

