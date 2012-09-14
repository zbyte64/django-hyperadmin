from django.views import generic
from django.contrib.auth import logout

from hyperadmin.hyperobjects import Link
from hyperadmin.resources.views import ResourceViewMixin

class AuthenticationResourceView(ResourceViewMixin, generic.View):
    view_class = 'login'
    
    def get_form_kwargs(self, **defaults):
        defaults['request'] = self.request
        return defaults
    
    def get_form_class(self):
        return self.resource.form_class
    
    def get_form(self, **kwargs):
        form_class = self.get_form_class()
        form = form_class(**kwargs)
        return form
    
    def get_items(self):
        return [self.request.user]
    
    def get_object(self):
        return self.request.user
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_active_link())
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_active_link(**form_kwargs)
        return self.resource.generate_update_response(self.get_response_media_type(), self.get_response_type(), form_link)
    
    def delete(self, request, *args, **kwargs):
        logout(request)
        return self.resource.generate_delete_response(self.get_response_media_type(), self.get_response_type())
    
    def get_login_link(self, **form_kwargs):
        form_class = self.get_form_class()
        form_kwargs.update(self.get_form_kwargs())
        form = form_class(**form_kwargs)
        
        login_link = Link(url=self.request.path,
                          resource=self.resource,
                          method='POST', #TODO should this be put?
                          form=form,
                          prompt='authenticate',
                          rel='create',)
        return login_link
    
    def get_logout_link(self, **form_kwargs):
        logout_link = Link(url=self.request.path,
                           resource=self.resource,
                               method='DELETE',
                               prompt='logout',
                               rel='delete',)
        return logout_link
    
    def get_active_link(self, **form_kwargs):
        if self.request.user.is_authenticated():
            return self.get_logout_link(**form_kwargs)
        return self.get_login_link(**form_kwargs)
    
    def get_ln_links(self, instance=None):
        links = super(AuthenticationResourceView, self).get_ln_links(instance)
        links.append(self.get_active_link())
        return links

class AuthenticationLogoutView(ResourceViewMixin, generic.View):
    view_class = 'logout'
    
    def get(self, request, *args, **kwargs):
        logout(request)
        return self.resource.generate_delete_response(self.get_response_media_type(), self.get_response_type())

