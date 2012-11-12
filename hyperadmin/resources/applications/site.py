from django.conf.urls.defaults import patterns, url, include

from hyperadmin.resources import BaseResource
from hyperadmin.resources.applications import views
from hyperadmin.resources.applications.forms import ViewResourceForm

class SiteResource(BaseResource):
    resource_class = 'resourcelisting'
    list_view = views.SiteResourceView
    form_class = ViewResourceForm
    
    def __init__(self, auth_resource=None, **kwargs):
        super(SiteResource, self).__init__(resource_adaptor=dict(), **kwargs)
        if auth_resource is None:
            from hyperadmin.resources.auth.auth import AuthResource
            auth_resource = AuthResource
        self.auth_resource = auth_resource(**kwargs)
    
    def get_prompt(self):
        return self.site.name
    
    def get_app_name(self):
        return self.site.name
    app_name = property(get_app_name)
    
    def get_view_endpoints(self):
        endpoints = super(SiteResource, self).get_view_endpoints()
        init = self.get_view_kwargs()
        
        list_view = {
            'url': r'^$',
            'view': self.list_view.as_view(**init),
            'name': 'index',
        }
        endpoints.append(list_view)
        
        return endpoints
    
    def get_urls(self):
        urlpatterns = super(SiteResource, self).get_urls()
        urlpatterns += patterns('',
            url(r'^-authentication/',
                include(self.auth_resource.urls)),
        )
        for key, app in self.applications.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(app.urls))
            )
        return urlpatterns
    
    def get_item_prompt(self, item):
        return item.instance.get_prompt()
    
    def get_items(self):
        applications = self.applications.items()
        apps = [entry[1] for entry in sorted(applications, key=lambda x: x[0])]
        all_apps = list()
        for app in apps:
            all_apps.append(app)
            all_apps.extend(app.get_items())
        all_apps.append(self.auth_resource)
        return all_apps
    
    def get_resource_items(self):
        return [self.get_resource_item(item) for item in self.get_items()]
    
    def get_item_url(self, item):
        if hasattr(item.instance, 'get_absolute_url'):
            return item.instance.get_absolute_url()
    
    def get_item_outbound_links(self, item):
        links = super(SiteResource, self).get_item_outbound_links(item)
        links.extend(item.instance.get_outbound_links())
        return links
    
    def get_absolute_url(self):
        return self.reverse('index')
    
    @property
    def applications(self):
        return self.site.applications

