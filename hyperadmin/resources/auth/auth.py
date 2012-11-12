from django.contrib.auth import logout

from hyperadmin.hyperobjects import Link, ResourceItem
from hyperadmin.resources import BaseResource
from hyperadmin.resources.auth import views
from hyperadmin.resources.auth.forms import AuthenticationResourceForm


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
        init = self.get_view_kwargs()
        
        endpoints.append({
            'url': r'^$',
            'view': self.detail_view.as_view(**init),
            'name': 'authentication',
        })
        endpoints.append({
            'url': r'^logout/$',
            'view': self.logout_view.as_view(**init),
            'name': 'logout',
        })
        
        return endpoints
    
    def api_permission_check(self, request):
        return None #resource is accessible to all
    
    def get_absolute_url(self):
        return self.reverse('authentication')
    
    def handle_login_submission(self, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            form.save()
            self.state['authenticated'] = True
            return self.site.site_resource.get_resource_link()
        return link.clone(form=form)
    
    def handle_logout_submission(self, link, submit_kwargs):
        logout(self.state['request'])
        self.state['authenticated'] = False
        return self.get_login_link()
    
    def get_login_link(self, form_kwargs=None, **kwargs):
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.get_form_kwargs(**form_kwargs)
        
        link_kwargs = {'url':self.reverse('authentication'),
                       'resource':self,
                       'on_submit':self.handle_login_submission,
                       'method':'POST',
                       'form_kwargs':form_kwargs,
                       'form_class': self.get_form_class(),
                       'prompt':'Login',
                       'rel':'login',}
        link_kwargs.update(kwargs)
        login_link = Link(**link_kwargs)
        return login_link
    
    def get_logout_link(self, form_kwargs=None, **kwargs):
        link_kwargs = {'url':self.reverse('logout'),
                       'resource':self,
                       'on_submit':self.handle_logout_submission,
                       'method':'POST',
                       'prompt':'Logout',
                       'rel':'logout',}
        link_kwargs.update(kwargs)
        login_link = Link(**link_kwargs)
        return login_link
    
    def get_restful_logout_link(self, form_kwargs=None, **kwargs):
        kwargs['url'] = self.reverse('authentication')
        kwargs['method'] = 'DELETE'
        return self.get_logout_link(form_kwargs, **kwargs)
    
    def get_idempotent_links(self):
        links = super(AuthResource, self).get_idempotent_links()
        if self.state.get('authenticated', False):
            links.append(self.get_restful_logout_link())
        else:
            links.append(self.get_login_link())
        return links
    
    def get_embedded_links(self):
        links = super(AuthResource, self).get_embedded_links()
        if self.state.get('authenticated', False):
            links.append(self.get_logout_link())
        return links

