from django.utils.translation import ugettext as _
from django.views import generic
from django import http

import mimeparse

from hyperadmin.models import log_action, ADDITION, CHANGE, DELETION
from links import Link

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
    resource_site = None
    
    def get_content_type(self):
        return mimeparse.best_match(
            self.resource_site.media_types.keys(), 
            self.request.META.get('HTTP_ACCEPT', '')
        )
    
    def get_embedded_links(self, instance=None):
        return self.resource.get_embedded_links(instance)
    
    def get_outbound_links(self, instance=None):
        return self.resource.get_outbound_links(instance)
    
    def get_templated_queries(self):
        return self.resource.get_templated_queries()
    
    #TODO find a better name
    def get_ln_links(self, instance=None):
        return self.resource.get_ln_links(instance)
    
    #TODO find a better name
    def get_li_links(self, instance=None):
        return self.resource.get_li_links(instance)
    
    def get_instance_url(self, instance):
        return self.resource.get_instance_url(instance)
    
    def get_items(self):
        return []
    
    def get_form_class(self, instance=None):
        return None

class ApplicationResourceView(ResourceViewMixin, generic.ListView):
    def get_items(self):
        return self.resource.get_items(self.request)
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self)

class SiteResourceView(ApplicationResourceView, generic.TemplateView):
    template_name = 'hyperadmin/index.html'
    
    def get_template_names(self):
        return [self.template_name]
    
    def get(self, request, *args, **kwargs):
        try:
            self.resource.get_media_type(self)
        except ValueError, e:
            return generic.TemplateView.get(self, request, *args, **kwargs)
        return ApplicationResourceView.get(self, request, *args, **kwargs)

class ModelResourceViewMixin(ResourceViewMixin, generic.edit.ModelFormMixin):
    form_class = None
    model = None
    queryset = None
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request)
    
    def get_items(self, **kwargs):
        return self.get_queryset()
    
    def get_items_forms(self, **kwargs):
        return [self.get_form(instance=item) for item in self.get_items()]
    
    def get_form_class(self, instance=None):
        return generic.edit.ModelFormMixin.get_form_class(self)
    
    def get_form(self, **kwargs):
        form_class = self.get_form_class()
        form = form_class(**kwargs)
        return form
    
    #form_valid & form_invalid should not be used

class ModelListResourceView(ModelResourceViewMixin, generic.CreateView):
    #TODO support pagination
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self)
    
    def post(self, request, *args, **kwargs):
        return self.resource.generate_create_response(self, form_class=self.get_form_class())
    
    def get_ln_links(self, instance=None):
        form = self.get_form(instance=instance)
        update_link = Link(url=self.request.path,
                           method='POST', #TODO should this be put?
                           form=form,)
        return [update_link] + super(ModelListResourceView, self).get_ln_links(instance)

class ModelDetailResourceView(ModelResourceViewMixin, generic.UpdateView):
    #TODO get_form retrieves information from mediatype
    
    def get_items(self, **kwargs):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return [self.object]
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_response(self, instance=self.object)
    
    def post(self, request, *args, **kwargs):
        # Workaround browsers not being able to send a DELETE method.
        #if request.POST.get('DELETE', None) == "DELETE":
        #    request.method = 'DELETE'
        #    return self.delete(request, *args, **kwargs)
        self.object = self.get_object()
        return self.resource.generate_update_response(self, instance=self.object, form_class=self.get_form_class())
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete():
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        with log_action(request.user, self.object, DELETION, request=request):
            self.object.delete()
        
        return self.resource.generate_delete_response(self)
    
    def get_ln_links(self, instance=None):
        links = super(ModelDetailResourceView, self).get_ln_links(instance)
        assert instance
        if instance:
            form = self.get_form(instance=instance)
            update_link = Link(url=self.request.path,
                               method='POST',
                               form=form,)
            return [update_link] + links
        return links

class InlineModelMixin(object):
    def get_parent(self):
        queryset = self.resource.parent_resource.get_queryset(self.request)
        parent = queryset.get(pk=self.kwargs['pk'])
        return parent
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request, instance=self.get_parent())

class InlineModelListResourceView(InlineModelMixin, ModelListResourceView):
    pass

class InlineModelDetailResourceView(InlineModelMixin, ModelDetailResourceView):
    def get_object(self):
        queryset = self.get_queryset()
        return queryset.objects.get(pk=self.kwargs['inline_pk'])

