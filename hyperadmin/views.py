from django import http
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.cache import add_never_cache_headers
from django.utils.translation import ugettext_lazy as _

from hyperadmin.links import Link


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
    #state = None
    global_state = None
    cacheable = False
    submit_methods = ['POST', 'PUT', 'DELETE']
    template_name = None
    
    def get_template_names(self):
        if self.template_name:
            if isinstance(self.template_name, basestring):
                template_names = [self.template_name]
            else:
                template_names = self.template_name
            return self.expand_template_names(template_names)
        return None
    
    def get_request_form_kwargs(self):
        return self.api_request.payload
    
    def get_item(self):
        return None
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        Takes a django request object and builds an APIRequest object
        Calls dispatch_api with the api request
        :rtype: HttpResponse
        """
        assert not self.api_request
        api_request = self.create_apirequest(request=request, url_args=args, url_kwargs=kwargs)
        endpoint = api_request.get_endpoint(self.get_url_name())
        return endpoint.dispatch_api(api_request)
    
    def internal_dispatch(self, **kwargs):
        '''
        Can be called directly to execute an API call. kwargs are passed to the intenral api request.
        '''
        assert not self.api_request
        api_request = self.create_internal_apirequest(**kwargs)
        endpoint = api_request.get_endpoint(self.get_url_name())
        return endpoint.dispatch_api(api_request)
    
    def dispatch_api(self, api_request):
        '''
        Execute the api request
        :rtype: HttpResponse
        '''
        response = self.generate_api_response(api_request)
        return self.normalize_response(response)
    
    def generate_api_response(self, api_request):
        '''
        Returns the result of executing a link
        :rtype: Link or HttpResponse
        '''
        if api_request.method.lower() in self.http_method_names:
            handler = getattr(self, api_request.method.lower(), self.handle_link_submission)
        else:
            handler = self.http_method_not_allowed
        self.api_request = api_request
        self.args = api_request.url_args
        self.kwargs = api_request.url_kwargs
        
        self.initialize_state()
        
        assert self.state is not None
        
        self.common_state.update(self.get_common_state_data())
        
        permission_response = self.api_permission_check(api_request, self)
        if permission_response is not None:
            return permission_response
        else:
            return handler(api_request)
    
    def normalize_response(self, response_or_link):
        '''
        Converts a link response to an HttpResponse
        :rtype: HttpResponse
        '''
        if isinstance(response_or_link, Link):
            #TODO TemplateResponse with a link
            response = self.generate_response(response_or_link)
        else:
            response = response_or_link
        if not self.cacheable and isinstance(response, http.HttpResponse):
            add_never_cache_headers(response)
        return response
    
    def get_common_state_data(self):
        """
        Return state data that should be available at the resource level for processing the api request
        """
        return {}
    
    def handle_link_submission(self, api_request):
        """
        Looks up the appropriate link for the HTTP Method and returns 
        the link.
        If Method is in `self.submit_methods` then return the result of
        submitting the link.
        """
        method = api_request.method.upper()
        proto = self.get_link_prototype_for_method(method)
        
        if proto:
            if proto.show_link():
                kwargs = {'use_request_url':True}
                if method in self.submit_methods:
                    #TODO other kwargs may be added
                    kwargs['form_kwargs'] = api_request.payload
                kwargs = self.get_link_kwargs(**kwargs)
                link = proto.get_link(**kwargs)
                if method in self.submit_methods:
                    response_link = link.submit()
                    return response_link
                return link
            else:
                return http.HttpResponseForbidden(_(u"You may not access this endpoint"))
        return http.HttpResponseBadRequest(_(u"Method %s is not allowed") % method)
    
    def options(self, api_request):
        links = self.get_available_links()
        return self.generate_options_response(links=links)
