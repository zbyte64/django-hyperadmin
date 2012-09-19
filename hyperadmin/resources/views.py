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
    
    def get_request_media_type(self):
        content_type = self.get_request_type()
        media_type_cls = self.resource_site.media_types.get(content_type, None)
        if media_type_cls is None:
            raise ValueError('Unrecognized request content type: %s' % content_type)
        return media_type_cls(self)
    
    def get_response_media_type(self):
        content_type = self.get_response_type()
        media_type_cls = self.resource_site.media_types.get(content_type, None)
        if media_type_cls is None:
            raise ValueError('Unrecognized response content type: %s' % content_type)
        return media_type_cls(self)
    
    def get_request_form_kwargs(self):
        media_type = self.get_request_media_type()
        form_kwargs = media_type.deserialize()
        return form_kwargs
    
    def get_item(self):
        return None
    
    def get_meta(self):
        return {}
    
    def get_state_class(self):
        return self.resource.get_state_class()
    
    def get_state_data(self):
        return {'auth':self.request.user,
                'resource':self.resource,
                'view_class':self.view_class,
                'item':self.get_item(),
                'filter_params':self.request.GET.copy(),}
    
    def get_state(self):
        state_cls = self.get_state_class()
        return state_cls(self.resource,
                     self.get_meta(),
                     self.get_state_data(),)
    
    @property
    def state(self):
        if not hasattr(self, '_state'):
            self._state = self.get_state()
        return self._state

