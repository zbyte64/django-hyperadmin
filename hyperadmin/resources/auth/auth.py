from hyperadmin.resources import BaseResource
from hyperadmin.resources.auth import views
from hyperadmin.resources.auth.forms import AuthenticationResourceForm
from hyperadmin.resources.auth.endpoints import LoginEndpoint, LogoutEndpoint


class AuthResource(BaseResource):
    form_class = AuthenticationResourceForm
    
    detail_view = views.AuthenticationResourceView
    logout_view = views.AuthenticationLogoutView
    
    def __init__(self, **kwargs):
        self._app_name = kwargs.pop('app_name', '-authentication')
        self._resource_name = kwargs.pop('resource_name', 'auth')
        kwargs.setdefault('resource_adaptor', None)
        super(AuthResource, self).__init__(**kwargs)
    
    def get_app_name(self):
        return self._app_name
    app_name = property(get_app_name)
    
    def get_resource_name(self):
        return self._resource_name
    resource_name = property(get_resource_name)
    
    def get_prompt(self):
        return self.resource_name
    
    def get_view_endpoints(self):
        endpoints = super(AuthResource, self).get_view_endpoints()
        endpoints.extend([
            LoginEndpoint(resource=self),
            LogoutEndpoint(resource=self),
        ])
        return endpoints
    
    def api_permission_check(self, request):
        return None #resource is accessible to all
    
    def get_absolute_url(self):
        return self.link_prototypes['login'].get_url()
