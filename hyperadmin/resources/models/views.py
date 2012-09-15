from django.utils.translation import ugettext as _
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django import http

from hyperadmin.resources.views import CRUDResourceViewMixin

class ModelResourceView(CRUDResourceViewMixin, View):
    model = None
    queryset = None
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request.user)
    
    def get_changelist(self):
        return self.resource.get_changelist(self.request.user, self.request.GET)

class ModelCreateResourceView(ModelResourceView):
    view_class = 'change_form'
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_create_link(), meta=self.get_meta())
    
    def post(self, request, *args, **kwargs):
        if not self.can_add():
            return http.HttpResponseForbidden(_(u"You may add an object"))
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_create_link(**form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, meta=self.get_meta())

class ModelListResourceView(ModelCreateResourceView):
    view_class = 'change_list'
    
    def get_state(self):
        state = super(ModelListResourceView, self).get_state()
        state['changelist'] = self.get_changelist()
        return state
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_restful_create_link(), meta=self.get_meta())
    
    def get_meta(self):
        resource_item = self.resource.get_resource_item(None, from_list=True)
        form = resource_item.get_form()
        data = dict()
        data['display_fields'] = list()
        for field in form:
            data['display_fields'].append({'prompt':field.label})
        changelist = self.state['changelist']
        data['object_count'] = changelist.paginator.count
        data['number_of_pages'] = changelist.paginator.num_pages
        return data
    
    def get_resource_item(self, instance):
        return self.resource.get_resource_item(instance, from_list=True)

class ModelDetailMixin(SingleObjectMixin):
    def get_resource_item(self):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return self.resource.get_resource_item(self.object)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        resource_item = self.get_resource_item()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_update_link(resource_item), meta=self.get_meta())

class ModelDeleteResourceView(ModelDetailMixin, ModelResourceView):
    view_class = 'delete_confirmation'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete(self.object):
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        resource_item = self.get_resource_item()
        
        form_link = self.get_delete_link(resource_item)
        response_link = form_link.submit()
        
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)

class ModelDetailResourceView(ModelDetailMixin, ModelResourceView):
    view_class = 'change_form'
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        resource_item = self.get_resource_item()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_update_link(resource_item), meta=self.get_meta())
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_change(self.object):
            return http.HttpResponseForbidden(_(u"You may not modify that object"))
        
        resource_item = self.get_resource_item()
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_update_link(resource_item, **form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, meta=self.get_meta())
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete(self.object):
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        resource_item = self.get_resource_item()
        form_link = self.get_delete_link(resource_item)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)

class InlineModelMixin(object):
    def get_changelist_links(self):
        return []
    
    def get_parent(self):
        queryset = self.resource.parent.get_queryset(self.request.user)
        parent = queryset.get(pk=self.kwargs['pk'])
        return parent
    
    def get_queryset(self):
        return self.resource.get_queryset(self.get_parent(), self.request.user)

class InlineModelCreateResourceView(InlineModelMixin, ModelCreateResourceView):
    pass

class InlineModelListResourceView(InlineModelMixin, ModelListResourceView):
    def get_changelist(self):
        if not hasattr(self, '_changelist'):
            self._changelist = self.resource.get_changelist(self.get_parent(), self.request.user, self.request.GET)
        return self._changelist

class InlineModelDetailMixin(object):
    def get_object(self):
        queryset = self.get_queryset()
        return queryset.get(pk=self.kwargs['inline_pk'])

class InlineModelDeleteResourceView(InlineModelDetailMixin, InlineModelMixin, ModelDeleteResourceView):
    pass

class InlineModelDetailResourceView(InlineModelDetailMixin, InlineModelMixin, ModelDetailResourceView):
    pass

