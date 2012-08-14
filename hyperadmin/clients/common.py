from django.conf.urls.defaults import patterns, url
from django.views.generic import TemplateView

class Client(object):
    def __init__(self, name='hyper-client', app_name='client'):
        self.name = name
        self.app_name = app_name
    
    def get_urls(self):
        pass
    
    def urls(self):
        return self.get_urls(), self.app_name, self.name
    urls = property(urls)

class TemplateClient(Client):
    template_name = None
    template_view = TemplateView
    
    def get_media(self):
        pass #TODO
    
    def get_context(self):
        return {'media':self.get_media()}
    
    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$',
                self.template_view.as_view(template_name=self.template_name),
                name='index'),
        )
        return urlpatterns

