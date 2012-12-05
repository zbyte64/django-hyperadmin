from django import http
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.cache import add_never_cache_headers

import mimeparse

from hyperadmin.states import EndpointState, push_session


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

class GetPatchMetaMixin(object):
    get_to_meta_map = {
        '_HTTP_ACCEPT':'HTTP_ACCEPT',
        '_CONTENT_TYPE':'CONTENT_TYPE',
    }
    
    @property
    def patched_meta(self):
        if not hasattr(self, '_patched_meta'):
            self._patched_meta = dict(self.request.META)
            for src, dst in self.get_to_meta_map.iteritems():
                if src in self.request.GET:
                    self._patched_meta[dst] = self.request.GET[src]
        return self._patched_meta
    
    def get_state_data(self):
        data = dict()
        pass_through_params = dict()
        for src, dst in self.get_to_meta_map.iteritems():
            if src in self.request.GET:
                pass_through_params[src] = self.request.GET[src]
        data['extra_get_params'] = pass_through_params
        return data

class ResourceViewMixin(GetPatchMetaMixin, ConditionalAccessMixin):
    resource = None
    resource_site = None
    endpoint = None
    global_state = None
    state_class = EndpointState
    view_class = None
    view_classes = []
    cacheable = False
    
    def get_response_type(self, patch_meta=True):
        if patch_meta:
            src = self.patched_meta
        else:
            src = self.request.META
        val = src.get('HTTP_ACCEPT', '')
        media_types = self.resource_site.media_types.keys()
        if not media_types:
            return val
        return mimeparse.best_match(media_types, val) or val
    
    def get_request_type(self, patch_meta=True):
        if patch_meta:
            src = self.patched_meta
        else:
            src = self.request.META
        val = src.get('CONTENT_TYPE', src.get('HTTP_ACCEPT', ''))
        media_types = self.resource_site.media_types.keys()
        if not media_types:
            return val
        return mimeparse.best_match(media_types, val) or val
    
    def get_request_media_type(self):
        content_type = self.get_request_type()
        media_type_cls = self.resource_site.media_types.get(content_type, None)
        if media_type_cls is None:
            raise ValueError('Unrecognized request content type "%s". Choices are: %s' % (content_type, self.resource_site.media_types.keys()))
        return media_type_cls(self)
    
    def get_response_media_type(self):
        content_type = self.get_response_type()
        media_type_cls = self.resource_site.media_types.get(content_type, None)
        if media_type_cls is None:
            raise ValueError('Unrecognized request content type "%s". Choices are: %s' % (content_type, self.resource_site.media_types.keys()))
        return media_type_cls(self)
    
    def generate_response(self, link):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), link, state=self.state)
    
    def get_request_form_kwargs(self):
        media_type = self.get_request_media_type()
        form_kwargs = media_type.deserialize()
        return form_kwargs
    
    def get_item(self):
        return None
    
    def get_meta(self):
        return {}
    
    def get_state_class(self):
        return self.state_class
    
    def get_view_classes(self):
        view_classes = list(self.view_classes)
        view_classes.append(self.view_class)
        return view_classes
    
    def get_session_data(self):
        #TODO consult site object
        data = {'request': self.request}
        if hasattr(self.request, 'user'):
            data['auth'] = self.request.user
        return data
    
    def get_state_data(self):
        data = super(ResourceViewMixin, self).get_state_data()
        data.update(self.kwargs)
        data.update({'view_class':self.view_class,
                     'view_classes':self.get_view_classes(),
                     #'item':self.get_item(), #do this in initialize_state
                     'params':self.request.GET.copy(),
                     'args':self.args,})
        return data
    
    def get_state_kwargs(self):
        return {
            'resource': self.resource,
            'endpoint': self.endpoint,
            'data':self.get_state_data(),
            'meta':{},
        }
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        
        session_params = self.get_session_data()
        if self.global_state:
            session_params.update(self.global_state)
        with push_session(session_params):
            self.initialize_state()
            
            #resource_params = dict(self.state)
            #resource_params['endpoint_state'] = self.state
            #with self.resource.state.patch_state(**resource_params):
            if True:
                #TODO anything we return must preserve the state @-@
                self.pre_dispatch()
                permission_response = self.resource.api_permission_check(self.request)
                if permission_response is not None:
                    return permission_response
                response = self.dispatch_api(request, *args, **kwargs)
                if not self.cacheable:
                    add_never_cache_headers(response)
                if hasattr(response, 'render'):
                    response.render()
                return response
    
    def dispatch_api(self, request, *args, **kwargs):
        return super(ResourceViewMixin, self).dispatch(request, *args, **kwargs)
    
    def initialize_state(self):
        self.state = self.get_state_class()(**self.get_state_kwargs())
        self.endpoint.state = self.state
        self.state.meta = self.get_meta()
        return self.state
    
    def pre_dispatch(self):
        """
        Put actions that need to be done after the state is prepped but before the api call is made.
        Typically extra state manipulation can go here
        """
        pass
    
    @property
    def link_prototypes(self):
        return self.endpoint.link_prototypes
    
    def get_resource_item(self, instance):
        return self.endpoint.get_resource_item(instance)
