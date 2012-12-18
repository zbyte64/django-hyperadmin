from django.http import HttpResponse

from hyperadmin.mediatypes.common import MediaType


class PassthroughResponse(HttpResponse):
    def __init__(self, *args, **kwargs):
        self.link = kwargs.pop('link')
        self.state = kwargs.pop('state')
        super(PassthroughResponse, self).__init__(*args, **kwargs)

class Passthrough(MediaType):
    def handle_redirect(self, link):
        if self.request.method != 'GET':
            response = PassthroughResponse(link.get_absolute_url(), status=303)
            response['Location'] = link.get_absolute_url()
        else:
            response = PassthroughResponse(link.get_absolute_url(), status=302)
            response['Location'] = link.get_absolute_url()
        return response
    
    def detect_redirect(self, link):
        return False
        #TODO
        if link.get_absolute_url() != self.request.get_full_path():
            return True
        return False
    
    def serialize(self, request, content_type, link, state):
        if self.detect_redirect(link):
            return self.handle_redirect(link)
        return PassthroughResponse('Unavailable (passthrough media type)', content_type, link=link, state=state)
    
    def deserialize(self, request):
        #TODO should punt to the real media type
        return {'data':request.POST,
                'files':request.FILES,}
