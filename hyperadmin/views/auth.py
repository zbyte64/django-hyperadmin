from django.views import generic
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout, login

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

