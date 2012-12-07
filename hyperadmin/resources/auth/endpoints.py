from django.contrib.auth import logout

from hyperadmin.resources.endpoints import LinkPrototype, Endpoint


class LoginLinkPrototype(LinkPrototype):
    def show_link(self, **kwargs):
        return not self.common_state.get('authenticated', True) or self.state.session['auth'].is_anonymous()
    
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
            self.state.session['authenticated'] = True
            return self.on_success()
        return link.clone(form=form)
    
    def on_success(self):
        return self.resource.site.site_resource.get_resource_link()

class LogoutLinkPrototype(LinkPrototype):
    def show_link(self, **kwargs):
        return self.common_state.get('authenticated', False) or self.state.session['auth'].is_authenticated()
    
    def get_link_kwargs(self, **kwargs):
        kwargs = super(LogoutLinkPrototype, self).get_link_kwargs(**kwargs)
        
        link_kwargs = {'url':self.get_url(),
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'prompt':'Logout',
                       'rel':'logout',}
        link_kwargs.update(kwargs)
        return super(LogoutLinkPrototype, self).get_link_kwargs(**link_kwargs)
    
    def handle_submission(self, link, submit_kwargs):
        logout(self.state.session['request'])
        self.common_state['authenticated'] = False
        return self.on_success()
    
    def on_success(self):
        return self.endpoint.link_prototypes['login'].get_link()


class LoginEndpoint(Endpoint):
    name_suffix = 'login'
    url_suffix = r'^$'
    
    def get_view_class(self):
        return self.resource.detail_view
    
    def get_links(self):
        return {'login':LoginLinkPrototype(endpoint=self),
                'rest-logout':LogoutLinkPrototype(endpoint=self, link_kwargs={'method':'DELETE'}),}
    
    def get_outbound_links(self):
        links = self.create_link_collection()
        links.add_link('logout', link_factor='LO')
        return links

class LogoutEndpoint(Endpoint):
    name_suffix = 'logout'
    url_suffix = r'^logout/$'
    
    def get_view_class(self):
        return self.resource.logout_view
    
    def get_links(self):
        return {'logout':LogoutLinkPrototype(endpoint=self)}

