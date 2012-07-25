from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _
from django.views import generic
from django import forms
from django import http

import mimeparse

from hyperadmin.models import log_action, ADDITION, CHANGE, DELETION
from hyperadmin.models import RelList

class ConditionalAccessMixin(object):
    etag_function = None
    
    def check_etag(self, data):
        new_etag = self.etag_function and self.etag_function(data)
        if not new_etag:
            return
        if self.request.META.get('HTTP_IF_NONE_MATCH', None) == new_etag:
            raise http.HttpResponseNotModified()
        if self.request.META.get('HTTP_IF_MATCH', new_etag) != new_etag:
            raise http.HttpResponse(status=412) # Precondition Failed
        
    # def dispatch(self, request, *args, **kwargs):
    #     return super(ConditionalAccessMixin, self).dispatch(request, *args, **kwargs)

    
class ResourceViewMixin(ConditionalAccessMixin):
    resource = None
    
    @property
    def resource_site(self):
        return self.resource.site
    
    def get_content_type(self):
        return mimeparse.best_match(
            self.CONTENT_TYPES, 
            self.request.META.get('HTTP_ACCEPT', '')
        )
    
    def get_embedded_links(self, instance=None):
        return []
    
    def get_outbound_links(self, instance=None):
        return []
    
    def get_templated_queries(self, instance=None):
        return []
    
    def get_instance_url(self, instance):
        return None
    
    def get_items(self):
        return []
    
    def get_form_class(self, instance=None):
        return None

class ModelResourceViewMixin(ResourceViewMixin, generic.edit.ModelFormMixin):
    form = None
    model = None
    queryset = None
    
    def get_items(self, **kwargs):
        return self.get_queryset()
    
    def get_form_class(self, instance=None):
        return generic.edit.ModelFormMixin.get_form_class(self)
    
    def form_valid(self, form):
        self.object = form.save()
        return self.resource.generate_response(self, instance=self.object)
    
    def form_invalid(self, form):
        return self.resource.generate_response(self, errors=form.errors)

class ModelListResourceView(ModelResourceViewMixin, generic.CreateView):
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self)
    
    def form_valid(self, form):
        self.object = form.save()
        return self.resource.generate_create_response(self, instance=self.object)

class ModelDetailResourceView(ModelResourceViewMixin, generic.UpdateView):
    def get_items(self, **kwargs):
        return [self.object]
    
    def post(self, request, *args, **kwargs):
        # Workaround browsers not being able to send a DELETE method.
        if request.POST.get('DELETE', None) == "DELETE":
            request.method = 'DELETE'
            return self.delete(request, *args, **kwargs)
        return super(ModelDetailResourceView, self).post(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete():
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        with log_action(request.user, self.object, DELETION, request=request):
            self.object.delete()
        
        return self.resource.generate_delete_response(self)

