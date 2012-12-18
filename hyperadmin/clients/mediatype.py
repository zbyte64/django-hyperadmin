from copy import copy

from django.views.generic import View
from django.conf.urls import patterns

from hyperadmin.clients.common import Client


class EndpointProxy(View):
    endpoint = None
    endpoint_kwargs = {}
    
    def dispatch(self, request, *args, **kwargs):
        view = self.endpoint.get_view(**self.endpoint_kwargs)
        return view(request, *args, **kwargs)

class MediaTypeClient(Client):
    '''
    Allows you to overide specific media types and host the resulting API at a different location
    '''
    media_types = []
    
    def __init__(self, api_endpoint, name='hyper-client', app_name='client'):
        super(MediaTypeClient, self).__init__(api_endpoint, name=name, app_name=app_name)
    
    def get_media_types(self):
        media_types = dict(self.api_endpoint.media_types)
        for media_type_handler in self.media_types:
            for media_type in media_type_handler.recognized_media_types:
                media_types[media_type] = media_type_handler
        return media_types
    
    def get_urls(self):
        try:
            return self.traverse(self.api_endpoint.get_urls())
        except Exception as error:
            print error
            raise
    
    def get_endpoint_kwargs(self):
        return {
            'global_state': {
                'site': self,
            }
        }
    
    #TODO find a better name
    def traverse(self, urlpatterns):
        new_patterns = list()
        for entry in urlpatterns:
            entry = copy(entry)
            if hasattr(entry, '_callback') and hasattr(entry._callback, 'endpoint'):
                endpoint = entry._callback.endpoint
                entry._callback = EndpointProxy.as_view(endpoint=endpoint, endpoint_kwargs=self.get_endpoint_kwargs())
                entry._callback.endpoint = endpoint
            elif hasattr(entry, 'url_patterns'):
                entry._urlconf_module = self.traverse(entry.url_patterns)
            new_patterns.append(entry)
        return patterns('', *new_patterns)
    
    def generate_response(self, media_type, content_type, link, state):
        api_request = state.endpoint.api_request
        media_type = self.get_media_types().get(content_type, media_type)(api_request=api_request)
        return media_type.serialize(request=api_request.request, content_type=content_type, link=link, state=state)
