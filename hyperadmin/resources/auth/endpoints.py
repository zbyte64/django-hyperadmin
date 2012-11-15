from django.contrib.auth import logout

from hyperadmin.resources.endpoints import LinkPrototype, Endpoint


class LoginLinkPrototype(LinkPrototype):
    def get_link_kwargs(self, **kwargs):
        form_kwargs = kwargs.pop('form_kwargs', None)
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.resource.get_form_kwargs(**form_kwargs)
        
        link_kwargs = {'url':self.get_url(),
                       'resource':self.resource,
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_kwargs':form_kwargs,
                       'form_class': self.resource.get_form_class(),
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
    def show_link(self):
        return True
        return self.resource.has_add_permission()
    
    def get_link_kwargs(self, **kwargs):
        
        link_kwargs = {'url':self.get_url(),
                       'resource':self,
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'prompt':'Logout',
                       'rel':'logout',}
        link_kwargs.update(kwargs)
        return super(LogoutLinkPrototype, self).get_link_kwargs(**link_kwargs)
    
    def handle_submission(self, link, submit_kwargs):
        logout(self.state.session['request'])
        self.state.session['authenticated'] = False
        return self.on_success()
    
    def on_success(self):
        return self.resource.links['login'].get_link()


class LoginEndpoint(Endpoint):
    name_suffix = 'login'
    url_suffix = r'^$'
    
    def get_view_class(self):
        return self.resource.detail_view
    
    def get_links(self):
        return {'login':LoginLinkPrototype(endpoint=self),
                'rest-logout':LogoutLinkPrototype(endpoint=self, link_kwargs={'method':'DELETE'}),}
    
    def get_outbound_links(self):
        links = super(LoginEndpoint, self).get_outbound_links()
        if 'logout' in self.resource.links and self.resource.links['logout'].show_link():
            links.append(self.resource.links['logout'].get_link(link_factor='LO'))
        return links

class LogoutEndpoint(Endpoint):
    name_suffix = 'logout'
    url_suffix = r'^logout/$'
    
    def get_view_class(self):
        return self.resource.logout_view
    
    def get_links(self):
        return {'logout':LogoutLinkPrototype(endpoint=self)}

