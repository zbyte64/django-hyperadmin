from hyperadmin.clients.common import Client

from copy import deepcopy

class MediaTypeClient(Client):
    '''
    Allows you to overide specific media types and host the resulting API at a different location
    '''
    media_types = []
    
    def __init__(self, api_endpoint, name='hyper-client', app_name='client'):
        self._original_api_endpoint = api_endpoint
        api_endpoint = deepcopy(api_endpoint)
        api_endpoint.reverse = self.reverse
        super(MediaTypeClient, self).__init__(api_endpoint, name=name, app_name=app_name)
        self.register_media_types()
    
    def register_media_types(self):
        for media_type_handler in self.media_types:
            for media_type in media_type_handler.recognized_media_types:
                self.api_endpoint.register_media_type(media_type, media_type_handler)
    
    def get_urls(self):
        return self.api_endpoint.get_urls()
