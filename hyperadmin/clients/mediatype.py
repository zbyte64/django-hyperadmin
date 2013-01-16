from copy import copy

from django.conf.urls import patterns

from hyperadmin.clients.common import Client
from hyperadmin.endpoints import RootEndpoint


class MediaTypeRootEndpoint(RootEndpoint):
    inner_api_endpoint = None
    client = None
    
    def __init__(self, **kwargs):
        super(MediaTypeRootEndpoint, self).__init__(**kwargs)
        self.media_types = self.client.get_media_types()
    
    def get_api_request_kwargs(self, **kwargs):
        params = {'site':self.get_inner_api_endpoint()}
        params.update(kwargs)
        return params
    
    def get_inner_api_endpoint(self):
        if not hasattr(self, 'bound_inner_api_endpoint'):
            new_attrs = {
                'get_api_request_kwargs':self.get_api_request_kwargs,
                'media_types':self.media_types,
                'reverse':self.reverse,
            }
            self.bound_inner_api_endpoint = self.inner_api_endpoint.fork(**new_attrs)
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
        self.endpoint = MediaTypeRootEndpoint(client=self, inner_api_endpoint=api_endpoint, namespace=name, app_name=app_name)
    
    def get_media_types(self):
        media_types = dict(self.api_endpoint.media_types)
        for media_type_handler in self.media_types:
            for media_type in media_type_handler.recognized_media_types:
                media_types[media_type] = media_type_handler
        return media_types
    
    def wrap_urls(self, urlpatterns):
        new_patterns = list()
        for entry in urlpatterns:
            entry = copy(entry)
            if hasattr(entry, '_callback') and hasattr(entry._callback, 'endpoint'):
                endpoint = entry._callback.endpoint
                entry._callback = endpoint.get_view(site=self.endpoint)
                entry._callback.endpoint = endpoint
            elif hasattr(entry, 'url_patterns'):
                entry._urlconf_module = self.wrap_urls(entry.url_patterns)
            new_patterns.append(entry)
        return patterns('', *new_patterns)
    
    def get_urls(self):
        try:
            return self.wrap_urls(self.endpoint.get_urls())
        except Exception as error:
            self.get_logger().exception('Unabled to load client urls')
            raise

