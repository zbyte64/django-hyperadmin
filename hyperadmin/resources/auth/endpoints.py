from django.contrib.auth import logout
from django import forms

from hyperadmin.links import LinkPrototype
from hyperadmin.resources.endpoints import ResourceEndpoint


class LoginLinkPrototype(LinkPrototype):
    def show_link(self, **kwargs):
        return True
        return not self.common_state.get('authenticated', True) or self.api_request.user.is_anonymous()
    
    def get_link_kwargs(self, **kwargs):
        kwargs = super(LoginLinkPrototype, self).get_link_kwargs(**kwargs)
        
        link_kwargs = {'url':self.get_url(),
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_class': self.get_form_class(),
                       'prompt':'Login',
                       'rel':'login',}
        link_kwargs.update(kwargs)
        return super(LoginLinkPrototype, self).get_link_kwargs(**link_kwargs)
    
    def handle_submission(self, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            form.save()
            self.common_state['authenticated'] = True
            return self.on_success()
        return link.clone(form=form)
    
    def on_success(self):
        return self.resource.site.get_link()

class LogoutLinkPrototype(LinkPrototype):
    def get_form_class(self):
        return forms.Form
    
    def get_form_kwargs(self, **kwargs):
        return {}
    
    def show_link(self, **kwargs):
        return self.common_state.get('authenticated', False) or self.api_request.user.is_authenticated()
    
    def get_link_kwargs(self, **kwargs):
        kwargs = super(LogoutLinkPrototype, self).get_link_kwargs(**kwargs)
        
        link_kwargs = {'url':self.get_url(),
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_class': self.get_form_class(),
                       'prompt':'Logout',
                       'rel':'logout',}
        link_kwargs.update(kwargs)
        return super(LogoutLinkPrototype, self).get_link_kwargs(**link_kwargs)
    
    def handle_submission(self, link, submit_kwargs):
        logout(self.api_request.request)
        self.common_state['authenticated'] = False
        return self.on_success()
    
    def on_success(self):
        return self.endpoint.resource.link_prototypes['login'].get_link()


class AuthMixin(object):
    def get_common_state_data(self):
        state = super(AuthMixin, self).get_common_state_data()
        state['authenticated'] = self.api_request.user.is_authenticated()
        return state
    
    def get_form_kwargs(self, **defaults):
        defaults['request'] = self.api_request.request
        return defaults

class LoginEndpoint(AuthMixin, ResourceEndpoint):
    name_suffix = 'login'
    url_suffix = r'^$'
    
    prototype_method_map = {
        'GET': 'login',
        'POST': 'login',
        'DELETE': 'rest-logout',
    }
    
    login_prototype = LoginLinkPrototype
    logout_prototype = LogoutLinkPrototype
    
    def get_link_prototypes(self):
        return [
            (self.login_prototype, {'name':'login'}),
            (self.logout_prototype, {'name':'rest-logout', 'link_kwargs':{'method':'DELETE'}}),
        ]
    
    def get_outbound_links(self):
        links = self.create_link_collection()
        links.add_link('logout', link_factor='LO')
        return links

class LogoutEndpoint(AuthMixin, ResourceEndpoint):
    name_suffix = 'logout'
    url_suffix = r'^logout/$'
    
    prototype_method_map = {
        'GET': 'logout',
        'POST': 'logout',
    }
    
    logout_prototype = LogoutLinkPrototype
    
    def get_link_prototypes(self):
        return [
            (self.logout_prototype, {'name':'logout'}),
        ]

