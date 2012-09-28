from django.template.response import TemplateResponse
from django.middleware.csrf import CsrfViewMiddleware

from common import MediaType

class Html5MediaType(MediaType):
    template_name = 'hyperadmin/html5/resource.html'
    template_dir_name = 'hyperadmin/html5'
    response_class = TemplateResponse
    recognized_media_types = [
        'text/html',
        'application/xhtml+xml',
        'application/text-html',
        'application/x-www-form-urlencoded',
        'multipart/form-data',
    ]
    
    def get_context_data(self, link, state):
        context = {'link':link,
                   'meta':state.meta,
                   'state':state,}
        
        resource_item = state.item
        
        context['namespaces'] = state.get_namespaces()
        
        if 'display_fields' in state.meta:
            context['display_fields'] = state.meta['display_fields']
        
        return context
    
    def get_template_names(self):
        params = {
            'base': self.template_dir_name,
            'view_class': self.view.view_class,
            'resource_name': getattr(self.resource, 'resource_name', None),
            'app_name': self.resource.app_name,
        }
        
        names = [
            '{base}/{app_name}/{resource_name}/{view_class}.html'.format(**params),
            '{base}/{app_name}/{view_class}.html'.format(**params),
            '{base}/{view_class}.html'.format(**params),
            self.template_name,
        ]
        
        return names
    
    def serialize(self, content_type, link, state):
        if self.detect_redirect(link):
            return self.handle_redirect(link)
        context = self.get_context_data(link=link, state=state)
        response = self.response_class(request=self.request, template=self.get_template_names(), context=context)
        response['Content-Type'] = 'text/html'
        return response
    
    def deserialize(self):
        self.check_csrf()
        
        return {'data':self.request.POST,
                'files':self.request.FILES,}
    
    def check_csrf(self):
        csrf_middleware = CsrfViewMiddleware()
        response = csrf_middleware.process_view(self.view.request, self.deserialize, self.view.args, self.view.kwargs)
        if response is not None:
            assert False, 'csrf failed' #TODO APIException(response) or SuspiciousOperation ....
            raise response

Html5MediaType.register_with_builtins()

