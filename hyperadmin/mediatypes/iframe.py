import mimeparse

from django.template.response import TemplateResponse
from django.middleware.csrf import CsrfViewMiddleware

from hyperadmin.mediatypes.common import MediaType


class IframeMediaType(MediaType):
    template_name = 'hyperadmin/iframe/resource.html'
    response_class = TemplateResponse
    recognized_media_types = [
        'text/html-iframe-transport;level=1',
    ]
    
    def get_response_type(self):
        response_type = self.view.patched_meta.get('HTTP_ACCEPT', '')
        effective_type = response_type.split(self.recognized_media_types[0], 1)[-1]
        return mimeparse.best_match(
            self.site.media_types.keys(),
            effective_type
        )
    
    def get_response_media_type(self):
        content_type = self.get_response_type()
        assert content_type not in self.recognized_media_types
        media_type_cls = self.site.media_types.get(content_type, None)
        if media_type_cls is None:
            raise ValueError('Unrecognized response content type: %s' % content_type)
        return media_type_cls(self.view)
    
    def get_context_data(self, link, state):
        media_type = self.get_response_media_type()
        content_type = self.get_response_type()
        response = media_type.serialize(content_type=content_type, link=link, state=state)
        context = {
            'payload':response.content,
            'content_type': content_type,
        }
        return context
    
    def get_template_names(self):
        return [self.template_name]
    
    def serialize(self, request, content_type, link, state):
        if self.detect_redirect(link):
            return self.handle_redirect(link)
        
        context = self.get_context_data(link=link, state=state)
        response = self.response_class(request=request, template=self.get_template_names(), context=context)
        response['Content-Type'] = 'text/html'
        return response
    
    def deserialize(self, request):
        self.check_csrf(request)
        
        return {'data':request.POST,
                'files':request.FILES,}
    
    def check_csrf(self, request):
        csrf_middleware = CsrfViewMiddleware()
        response = csrf_middleware.process_view(request, self.deserialize, self.view.args, self.view.kwargs)
        if response is not None:
            assert False, 'csrf failed' #TODO APIException(response) or SuspiciousOperation ....
            raise response

IframeMediaType.register_with_builtins()

