from django.utils.translation import ugettext as _
from django.views import generic
from django import http

from hyperadmin.models import log_action, DELETION

from common import ResourceViewMixin

class ModelResourceViewMixin(ResourceViewMixin, generic.edit.ModelFormMixin):
    form_class = None
    model = None
    queryset = None
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request)
    
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
    #TODO support pagination
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self)
    
    def form_valid(self, form):
        self.object = form.save()
        return self.resource.generate_create_response(self, instance=self.object)

class ModelDetailResourceView(ModelResourceViewMixin, generic.UpdateView):
    def get_items(self, **kwargs):
        return [self.object]
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_response(self)
    
    def post(self, request, *args, **kwargs):
        # Workaround browsers not being able to send a DELETE method.
        if request.POST.get('DELETE', None) == "DELETE":
            request.method = 'DELETE'
            return self.delete(request, *args, **kwargs)
        #TODO: return self.resource.generate_response(self, instance=self.object)
        return super(ModelDetailResourceView, self).post(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete():
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        with log_action(request.user, self.object, DELETION, request=request):
            self.object.delete()
        
        return self.resource.generate_delete_response(self)

