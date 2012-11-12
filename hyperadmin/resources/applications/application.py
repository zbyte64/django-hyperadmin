from django.conf.urls.defaults import patterns, url, include

from hyperadmin.resources import BaseResource
from hyperadmin.resources.applications import views
from hyperadmin.resources.applications.forms import ViewResourceForm

class ApplicationResource(BaseResource):
    resource_class = 'resourcelisting'
    list_view = views.ApplicationResourceView
    form_class = ViewResourceForm
    
    def __init__(self, app_name, **kwargs):
        super(ApplicationResource, self).__init__(resource_adaptor=dict(), **kwargs)
        self._app_name = app_name
    
    def get_app_name(self):
        return self._app_name
    app_name = property(get_app_name)
    
    def get_view_endpoints(self):
        endpoints = super(ApplicationResource, self).get_view_endpoints()
        init = self.get_view_kwargs()
        
        list_view = {
            'url': r'^$',
            'view': self.list_view.as_view(**init),
            'name': self.app_name,
        }
        endpoints.append(list_view)
        
        return endpoints
    
    def get_urls(self):
        urlpatterns = super(ApplicationResource, self).get_urls()
        for key, resource in self.resource_adaptor.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(resource.urls))
            )
        return urlpatterns
    
    def register_resource(self, resource):
        key = resource.get_resource_name()
        self.resource_adaptor[key] = resource
    
    def get_items(self):
        #TODO sort by name
        return self.resource_adaptor.values()
    
    def get_item_prompt(self, item):
        return item.instance.get_prompt()
    
    def get_item_url(self, item):
        if hasattr(item.instance, 'get_absolute_url'):
            return item.instance.get_absolute_url()
    
    def get_absolute_url(self):
        return self.reverse(self.app_name)
    
    def get_resource_items(self):
        return [self.get_resource_item(item) for item in self.get_items()]
    
    def get_item_outbound_links(self, item):
        links = super(ApplicationResource, self).get_item_outbound_links(item)
        links.extend(item.instance.get_outbound_links())
        return links
    
    def get_child_resource_links(self):
        links = list()
        for key, resource in self.resource_adaptor.iteritems():
            resource_link = resource.get_resource_link(rel='child-resource')
            links.append(resource_link)
        return links
    
    def get_prompt(self):
        return self.app_name.replace('-',' ').replace('_', ' ')
    
    def __unicode__(self):
        return u'App Resource: %s' % self.app_name

