from hyperadmin.hyperobjects import patch_global_state
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
            if endpoint['name'] == self.url_name:
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
            patch_params = self.get_global_state()
            #TODO patch_endpoint_state(params={})
            #TODO consider: patching global state should be silod to a particular api site
            with patch_global_state(**patch_params):
                api_args = self.get_api_args()
                api_kwargs = self.get_api_kwargs()
                self._api_response = endpoint['view'](self.request, *api_args, **api_kwargs)
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

#CONSIDER: should we expose CRUD functionality as default and have the process entirely controlled by permissions?

