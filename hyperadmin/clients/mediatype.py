from hyperadmin.clients.common import Client
from hyperadmin.hyperobjects import patch_global_state


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
        media_types = self.get_media_types()
        try:
            with patch_global_state(reverse=self.reverse, media_types=media_types) as state:
                urls = self.api_endpoint.get_urls()
                return urls
        except Exception as error:
            print error
            raise
