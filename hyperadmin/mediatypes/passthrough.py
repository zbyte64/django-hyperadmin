from django.http import HttpResponse

from hyperadmin.mediatypes.common import MediaType


class PassthroughResponse(HttpResponse):
    def __init__(self, *args, **kwargs):
        self.link = kwargs.pop('link')
        self.state = kwargs.pop('state')
        super(PassthroughResponse, self).__init__(*args, **kwargs)

class Passthrough(MediaType):
    def handle_redirect(self, link, content_type):
        if self.api_request.method != 'GET':
            status = 303
        else:
            status = 302
        response = PassthroughResponse(link.get_absolute_url(), status=status, content_type=content_type)
        response['Location'] = link.get_absolute_url()
        return response
    
    def detect_redirect(self, link):
        return False
        #TODO
        if link.get_absolute_url() != self.api_request.get_full_path():
            return True
        return False
    
    def serialize(self, content_type, link, state):
        if self.detect_redirect(link):
            return self.handle_redirect(link, content_type)
        return PassthroughResponse('Unavailable (passthrough media type)', content_type, link=link, state=state)
    
    def deserialize(self):
        #TODO should punt to the real media type
        request = self.get_django_request()
        return {'data':request.POST,
                'files':request.FILES,}
