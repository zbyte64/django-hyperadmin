from django.views import generic

from hyperadmin.resources.views import ResourceViewMixin

class AuthViewMixin(object):
    def get_form_kwargs(self, **defaults):
        defaults['request'] = self.request
        return defaults
    
    def get_login_link(self, **form_kwargs):
        form_kwargs.update(self.get_form_kwargs())
        return self.resource.get_login_link(**form_kwargs)
    
    def get_logout_link(self, **form_kwargs):
        form_kwargs.update(self.get_form_kwargs())
        return self.resource.get_logout_link(**form_kwargs)
    
    def get_active_link(self, **form_kwargs):
        if self.request.user.is_authenticated():
            return self.get_logout_link(**form_kwargs)
        return self.get_login_link(**form_kwargs)

class AuthenticationResourceView(AuthViewMixin, ResourceViewMixin, generic.View):
    view_class = 'login'
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_active_link())
    
    def post(self, request, *args, **kwargs):
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_active_link(**form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_update_response(self.get_response_media_type(), self.get_response_type(), response_link)
    
    def delete(self, request, *args, **kwargs):
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_logout_link(**form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_delete_response(self.get_response_media_type(), self.get_response_type(), response_link)
    
    def get_ln_links(self, instance=None):
        links = super(AuthenticationResourceView, self).get_ln_links(instance)
        links.append(self.get_active_link())
        return links

class AuthenticationLogoutView(AuthViewMixin, ResourceViewMixin, generic.View):
    view_class = 'logout'
    
    def get(self, request, *args, **kwargs):
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_logout_link(**form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_delete_response(self.get_response_media_type(), self.get_response_type(), response_link)

