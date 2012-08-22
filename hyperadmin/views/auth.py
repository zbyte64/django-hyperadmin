from django.views import generic
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout, login

from hyperadmin.resources.links import Link

from common import ResourceViewMixin

class AuthenticationResourceForm(AuthenticationForm):
    def save(self, commit=True):
        assert self.request
        user = self.get_user()
        login(self.request, user)
        return user

class AuthenticationResourceView(ResourceViewMixin, generic.View):
    form_class = AuthenticationForm
    
    def get_form_kwargs(self, **defaults):
        defaults['request'] = self.request
        return defaults
    
    def get_form_class(self):
        return self.form_class
    
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
        return self.resource.generate_response(self, instance=self.object)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_update_response(self, instance=self.object, form_class=self.get_form_class())
    
    def delete(self, request, *args, **kwargs):
        logout(request)
        return self.resource.generate_delete_response(self)
    
    def get_ln_links(self, instance=None):
        links = super(AuthenticationResourceView, self).get_ln_links(instance)
        if self.request.user.is_authenticated():
            logout_link = Link(url=self.request.path,
                               method='DELETE',
                               prompt='logout',
                               rel='delete',)
            links.append(logout_link)
        else:
            form = self.get_form()#instance=instance)
            login_link = Link(url=self.request.path,
                              method='POST', #TODO should this be put?
                              form=form,
                              prompt='authenticate',
                              rel='create',)
            links.append(login_link)
        return links

