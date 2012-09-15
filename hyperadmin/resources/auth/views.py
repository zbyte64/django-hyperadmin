from django.views.generic import View

from hyperadmin.resources.views import ResourceViewMixin

class AuthViewMixin(ResourceViewMixin):
    def get_state(self):
        state = super(AuthViewMixin, self).get_state()
        state['authenticated'] = self.request.user.is_authenticated()
        state['request'] = self.request #for logging in and out
        return state
    
    def get_form_kwargs(self, **defaults):
        defaults['request'] = self.request
        return defaults
    
    def get_login_link(self, **form_kwargs):
        form_kwargs.update(self.get_form_kwargs())
        return self.resource.get_login_link(form_kwargs=form_kwargs)
    
    def get_logout_link(self, **form_kwargs):
        form_kwargs.update(self.get_form_kwargs())
        return self.resource.get_logout_link(form_kwargs=form_kwargs)
    
    def get_restful_logout_link(self, **form_kwargs):
        form_kwargs.update(self.get_form_kwargs())
        return self.resource.get_restful_logout_link(form_kwargs=form_kwargs)
    
    def get_active_link(self, **form_kwargs):
        if self.request.user.is_authenticated():
            return self.get_logout_link(**form_kwargs)
        return self.get_login_link(**form_kwargs)

class AuthenticationResourceView(AuthViewMixin, View):
    view_class = 'login'
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_login_link(), self.state)
    
    def post(self, request, *args, **kwargs):
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_active_link(**form_kwargs)
        response_link = form_link.submit(self.state)
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, self.state)
    
    def delete(self, request, *args, **kwargs):
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_restful_logout_link(**form_kwargs)
        response_link = form_link.submit(self.state)
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, self.state)

class AuthenticationLogoutView(AuthViewMixin, View):
    view_class = 'logout'
    
    def get(self, request, *args, **kwargs):
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_logout_link(**form_kwargs)
        response_link = form_link.submit(self.state)
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, self.state)

