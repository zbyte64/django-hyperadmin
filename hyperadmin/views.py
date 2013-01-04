from django import http
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.cache import add_never_cache_headers
from django.utils.translation import ugettext_lazy as _

from hyperadmin.hyperobjects import Link
from hyperadmin.apirequests import HTTPAPIRequest


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
        
class EndpointViewMixin(ConditionalAccessMixin):
    state = None
    global_state = None
    cacheable = False
    
    def get_request_form_kwargs(self):
        return self.api_request.payload
    
    def get_item(self):
        return None
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        Takes a django request object and builds an APIRequest object
        Calls dispatch_api with the api request
        """
        api_request = HTTPAPIRequest(site=self.site, request=request, url_args=args, url_kwargs=kwargs)
        api_request.populate_session_data_from_request(request)
        if self.global_state is not None:
            api_request.session_state.update(self.global_state)
        return self.dispatch_api(api_request)
    
    def dispatch_api(self, api_request):
        if api_request.method.lower() in self.http_method_names:
            handler = getattr(self, api_request.method.lower(), self.handle_link_submission)
        else:
            handler = self.http_method_not_allowed
        self.api_request = api_request
        self.args = api_request.url_args
        self.kwargs = api_request.url_kwargs
        
        self.initialize_state()
        
        assert self.state is not None
        assert self.resource != self
        assert self.resource.state is not None
        assert self.common_state is not None #resource.state is not initialized!
        
        self.pre_dispatch()
        
        self.common_state.update(self.get_common_state_data())
        
        permission_response = self.api_permission_check(api_request)
        if permission_response is not None:
            response_or_link = permission_response
        else:
            response_or_link = handler(api_request)
        if isinstance(response_or_link, Link):
            #TODO TemplateResponse with a link
            response = self.generate_response(response_or_link)
        else:
            response = response_or_link
        if not self.cacheable:
            add_never_cache_headers(response)
        return response
    
    def get_common_state_data(self):
        """
        Return state data that should be available at the resource level for processing the api request
        """
        return {}
    
    def pre_dispatch(self):
        """
        Put actions that need to be done after the state is prepped but before the api call is made.
        Typically extra state manipulation can go here
        """
        pass
    
    def handle_link_submission(self, api_request):
        prototypes = self.get_link_prototypes()
        method = api_request.method.upper()
        if method in prototypes:
            proto = prototypes[method]
            if proto.show_link():
                kwargs = {'use_request_url':True}
                if method in ('POST', 'PUT', 'DELETE'):
                    #TODO other kwargs may be added
                    kwargs['form_kwargs'] = api_request.payload
                kwargs = self.get_link_kwargs(**kwargs)
                link = proto.get_link(**kwargs)
                if method in ('POST', 'PUT', 'DELETE'):
                    response_link = link.submit()
                    return response_link
                return link
            else:
                return http.HttpResponseForbidden(_(u"You may not access this endpoint"))
        return http.HtppResponseBadRequest(_(u"Method %s is not allowed") % method)
