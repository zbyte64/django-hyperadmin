from django.contrib.contenttypes.models import ContentType
from django import forms
from django.test.client import RequestFactory

from hyperadmin.resources.views import ResourceViewMixin

class BaseMockResourceView(ResourceViewMixin):
    content_type = 'text/html'
    
    def __init__(self, items=[]):
        self.items = items
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        from hyperadmin.resources.models.models import ModelResource
        from hyperadmin.sites import site
        self.resource = ModelResource(ContentType, site)
        ResourceViewMixin.__init__(self)
    
    def get_items(self, **kwargs):
        return self.items
    
    def get_content_type(self):
        return self.content_type
    
    def get_form_class(self, **kwargs):
        class GenForm(forms.ModelForm):
            class Meta:
                model = ContentType
        return GenForm
    
    def get_form_kwargs(self):
        return {}
    
    def get_form(self, **kwargs):
        form_class = self.get_form_class()
        form = form_class(**kwargs)
        return form
    
    def get_instance_url(self, instance):
        return None
    
    def get_embedded_links(self, instance=None):
        return []
    
    def get_outbound_links(self, instance=None):
        return []
    
    def get_templated_queries(self):
        return []
    
    def get_ln_links(self, instance=None):
        return []
    
    def get_li_links(self, instance=None):
        return []
