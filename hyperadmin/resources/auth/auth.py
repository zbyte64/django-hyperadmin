from django.conf.urls.defaults import patterns, url
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
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            return self.as_nonauthenticated_view(view, cacheable)
        
        init = self.get_view_kwargs()
        
        # Admin-site-wide views.
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.detail_view.as_view(**init)),
                name='authentication'),
            url(r'^logout/$',
                wrap(self.logout_view.as_view(**init)),
                name='logout'),
        )
        return urlpatterns
    
    def get_form_class(self):
        return self.form_class
    
    def get_instance_url(self, instance):
        return self.get_absolute_url()
    
    def get_absolute_url(self):
        return self.reverse('authentication')
    
    def handle_login_submission(self, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            return self.site.site_resource.get_resource_link()
        return self.get_login_link(form_kwargs=link.form_kwargs, form=form)
    
    def handle_logout_submission(self, link, submit_kwargs):
        logout(link.resource_item.instance)
        return self.get_login_link()
    
    def get_login_link(self, **form_kwargs):
        form_class = self.get_form_class()
        form_kwargs.update(self.get_form_kwargs())
        form = form_class(**form_kwargs)
        
        login_link = Link(url=self.reverse('authentication'),
                          resource_item=self.get_resource_item(form_kwargs['request']),
                          on_submit=self.handle_login_submission,
                          resource=self,
                          method='POST', #TODO should this be put?
                          form=form,
                          prompt='authenticate',
                          rel='login',)
        return login_link
    
    def get_logout_link(self, **form_kwargs):
        logout_link = Link(url=self.reverse('logout'),
                           resource=self,
                           resource_item=self.get_resource_item(form_kwargs['request']),
                           on_submit=self.handle_logout_submission,
                           method='POST',
                           prompt='logout',
                           rel='logout',)
        return logout_link

