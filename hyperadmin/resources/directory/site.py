from django.conf.urls.defaults import patterns, url, include

from hyperadmin.resources.directory.resources import ResourceDirectory

#gets replaced
class SiteResource(ResourceDirectory):
    resource_class = 'resourcelisting'
    auth_resource = None
    
    @property
    def auth_resource(self):
        return self.site.auth_resource
    
    def get_prompt(self):
        return self._site.name
    
    def get_app_name(self):
        return self._site.name
    app_name = property(get_app_name)
    
    def get_urls(self):
        urlpatterns = super(SiteResource, self).get_urls()
        urlpatterns += patterns('',
            url(r'^-authentication/',
                include(self.auth_resource.urls)),
        )
        return urlpatterns

