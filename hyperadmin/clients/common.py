try:
    from django.conf.urls import patterns, url
except ImportError:
    from django.conf.urls.defaults import patterns, url
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse

from hyperadmin.apirequests import InternalAPIRequest

import logging


class Client(object):
    default_namespace = 'hyper-client'
    default_app_name = 'client'
    
    def __init__(self, api_endpoint, name=None, app_name=None):
        self.api_endpoint = api_endpoint
        self.name = name or self.default_namespace
        self.app_name = app_name or self.default_app_name
    
    def get_logger(self):
        return logging.getLogger(__name__)
    
    def get_urls(self):
        pass
    
    def urls(self):
        return self, self.app_name, self.name
    urls = property(urls)
    
    @property
    def urlpatterns(self):
        return self.get_urls()
    
    def reverse(self, name, *args, **kwargs):
        return reverse('%s:%s' % (self.name, name), args=args, kwargs=kwargs, current_app=self.app_name)

class SimpleTemplateClientView(TemplateView):
    client = None
    
    def get_context_data(self, **kwargs):
        context = super(SimpleTemplateClientView, self).get_context_data(**kwargs)
        context.update(self.client.get_context_data())
        return context

class SimpleTemplateClient(Client):
    template_name = None
    template_view = SimpleTemplateClientView
    
    def get_media(self):
        pass #TODO
    
    def get_context_data(self):
        api_endpoint = self.api_endpoint
        if hasattr(api_endpoint, 'get_absolute_url'):
            api_request = InternalAPIRequest(site=api_endpoint)
            api_endpoint = api_endpoint.fork(api_request=api_request)
            api_endpoint = api_endpoint.get_absolute_url()
        return {'media':self.get_media(),
                'api_endpoint':api_endpoint,
                'client':self,}
    
    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$',
                self.template_view.as_view(template_name=self.template_name, client=self),
                name='index'),
        )
        return urlpatterns

