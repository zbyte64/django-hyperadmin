from hyperadmin.mediatypes.passthrough import Passthrough


class ClientMixin(object):
    """
    Contains logic for connecting to an endpoint on the API
    """
    resource = None
    url_name = None
    client_site = None
    
    def get_api_endpoint(self):
        for endpoint in self.resource.get_view_endpoints():
            if endpoint.name_suffix == self.url_name:
                return endpoint
    
    def get_api_kwargs(self):
        return dict(self.kwargs)
    
    def get_api_args(self):
        return list(self.args)
    
    def get_global_state(self):
        #with media type = pass through
        kwargs = {'media_types': {'*': Passthrough}}
        #patch permissions by setting your own client_site
        if self.client_site is not None:
            kwargs['site'] = self.client_site
        return kwargs
    
    def get_api_response(self):
        if not hasattr(self, '_api_response'):
            endpoint = self.get_api_endpoint()
            assert endpoint is not None, 'Failed to look up endpint for: %s in %s' % (self.url_name, [e['name'] for e in self.resource.get_view_endpoints()])
            
            api_args = self.get_api_args()
            api_kwargs = self.get_api_kwargs()
            self._api_response = endpoint.get_view()(self.request, *api_args, **api_kwargs)
        return self._api_response
    
    def get_state(self):
        return self.get_api_response().state
    
    def get_link(self):
        return self.get_api_response().link
    
    def get_context_data(self, **kwargs):
        context = super(ClientMixin, self).get_context_data(**kwargs)
        context['state'] = self.get_state()
        context['link'] = self.get_link()
        return context
    
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        #TODO use an alternative template response class instead
        patch_params = self.get_global_state()
        with self.client_site.state.patch_state(**patch_params):
            response = super(ClientMixin, self).dispatch(request, *args, **kwargs)
            if hasattr(response, 'render'):
                response.render()
            return response

#CONSIDER: should we expose CRUD functionality as default and have the process entirely controlled by permissions?

