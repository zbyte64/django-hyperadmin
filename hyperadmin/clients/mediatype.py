from hyperadmin.clients.common import Client
from hyperadmin.apirequests import HTTPAPIRequest
from hyperadmin.endpoints import RootEndpoint


class MediaTypeClientHTTPAPIRequest(HTTPAPIRequest):
    def get_site(self):
        """
        Returns the bound site
        
        :rtype: SiteResource
        """
        if 'site' not in self.endpoint_state:
            bound_site = self.site.fork(api_request=self)
            self.endpoint_state['site'] = bound_site
            bound_site.post_register()
        return self.endpoint_state['site']

class MediaTypeRootEndpoint(RootEndpoint):
    apirequest_class = MediaTypeClientHTTPAPIRequest
    inner_api_endpoint = None
    client = None
    
    def __init__(self, **kwargs):
        super(MediaTypeRootEndpoint, self).__init__(**kwargs)
        self.media_types = self.client.get_media_types()
    
    def get_inner_api_endpoint(self):
        if not hasattr(self, 'bound_inner_api_endpoint'):
            self.bound_inner_api_endpoint = self.inner_api_endpoint.fork(create_apirequest=self.create_apirequest)
        return self.bound_inner_api_endpoint
    
    def get_urls(self):
        return self.get_inner_api_endpoint().get_urls()

class MediaTypeClient(Client):
    '''
    Allows you to overide specific media types and host the resulting API at a different location
    '''
    media_types = []
    
    def __init__(self, api_endpoint, name='hyper-client', app_name='client'):
        super(MediaTypeClient, self).__init__(api_endpoint, name=name, app_name=app_name)
        self.endpoint = MediaTypeRootEndpoint(client=self, inner_api_endpoint=api_endpoint, name=name, app_name=app_name)
    
    def get_media_types(self):
        media_types = dict(self.api_endpoint.media_types)
        for media_type_handler in self.media_types:
            for media_type in media_type_handler.recognized_media_types:
                media_types[media_type] = media_type_handler
        return media_types
    
    def get_urls(self):
        try:
            return self.endpoint.get_urls()
        except Exception as error:
            print error
            raise

