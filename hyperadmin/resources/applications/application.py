from django.conf.urls.defaults import patterns, url, include

from hyperadmin.resources import BaseResource
from hyperadmin.resources.applications import views

class ApplicationResource(BaseResource):
    resource_class = 'resourcelisting'
    list_view = views.ApplicationResourceView
    
    def __init__(self, app_name, site):
        self._app_name = app_name
        self.resource_adaptor = dict() #TODO OrderedDict
        self.site = site
        self.parent = site.site_resource
    
    def get_app_name(self):
        return self._app_name
    app_name = property(get_app_name)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            return self.as_view(view, cacheable)
        
        init = self.get_view_kwargs()
        
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name=self.app_name),
        )
        for key, resource in self.resource_adaptor.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(resource.urls))
            )
        return urlpatterns
    
    def register_resource(self, resource):
        key = resource.get_resource_name()
        self.resource_adaptor[key] = resource
    
    def get_items(self, state):
        #TODO sort by name
        return self.resource_adaptor.values()
    
    def get_item_prompt(self, item):
        return item.instance.get_prompt()
    
    def get_item_url(self, item):
        if hasattr(item.instance, 'get_absolute_url'):
            return item.instance.get_absolute_url()
    
    def get_absolute_url(self):
        return self.reverse(self.app_name)
    
    def get_resource_items(self, state):
        return [self.get_resource_item(item) for item in self.get_items(state)]
        
    def get_child_resource_links(self):
        links = list()
        for key, resource in self.resource_adaptor.iteritems():
            resource_link = resource.get_resource_link(rel='child-resource')
            links.append(resource_link)
        return links
    
    def get_prompt(self):
        return self.app_name
    
    def __unicode__(self):
        return u'App Resource: %s' % self.app_name

