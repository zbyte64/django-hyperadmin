from hyperadmin.resources.views import ResourceViewMixin

from django.views.generic import View
from django import http


class CRUDResourceViewMixin(ResourceViewMixin):
    form_class = None
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        return self.resource.get_form_class()
    
    def get_form_kwargs(self):
        return {}
    
    def get_link_kwargs(self):
        return {}
    
    def can_add(self):
        return self.resource.has_add_permission(self.request.user)
    
    def can_change(self, instance=None):
        return self.resource.has_change_permission(self.request.user, instance)
    
    def can_delete(self, instance=None):
        return self.resource.has_delete_permission(self.request.user, instance)
    
    def get_create_link(self, **form_kwargs):
        form_kwargs.update(self.get_form_kwargs())
        link_kwargs = self.get_link_kwargs()
        link_kwargs.update({'form_class': self.get_form_class(),
                            'form_kwargs': form_kwargs,})
        return self.resource.get_create_link(**link_kwargs)
    
    def get_update_link(self, item, **form_kwargs):
        form_kwargs.update(self.get_form_kwargs())
        link_kwargs = self.get_link_kwargs()
        link_kwargs.update({'form_class': self.get_form_class(),
                            'form_kwargs': form_kwargs,
                            'item':item})
        return self.resource.get_update_link(**link_kwargs)
    
    def get_restful_update_link(self, item, **form_kwargs):
        form_kwargs.update(self.get_form_kwargs())
        link_kwargs = self.get_link_kwargs()
        link_kwargs.update({'form_class': self.get_form_class(),
                            'form_kwargs': form_kwargs,
                            'item':item})
        return self.resource.get_restful_update_link(**link_kwargs)
    
    def get_delete_link(self, item, **form_kwargs):
        return self.resource.get_delete_link(item=item, form_kwargs=form_kwargs)
    
    def get_restful_delete_link(self, item, **form_kwargs):
        return self.resource.get_restful_delete_link(item=item, form_kwargs=form_kwargs)
    
    def get_list_link(self):
        link_kwargs = self.get_link_kwargs()
        return self.resource.get_resource_link(**link_kwargs)

class CRUDView(CRUDResourceViewMixin, View):
    pass

class CRUDCreateView(CRUDView):
    view_class = 'change_form'
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_create_link())
    
    def post(self, request, *args, **kwargs):
        if not self.can_add():
            return http.HttpResponseForbidden(_(u"You may not add an object"))
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_create_link(**form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)

class CRUDListView(CRUDView):
    view_class = 'change_list'
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_list_link())
    
    def post(self, request, *args, **kwargs):
        if not self.can_add():
            return http.HttpResponseForbidden(_(u"You may not add an object"))
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_create_link(**form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)
    
    def get_meta(self):
        resource_item = self.resource.get_list_resource_item(None)
        form = resource_item.get_form()
        data = dict()
        data['display_fields'] = list()
        for field in form:
            data['display_fields'].append({'prompt':field.label})
        return data
    
    def fork_state(self):
        super(CRUDListView, self).fork_state()
        self.state['changelist'] = self.resource.get_changelist()
        if 'paginator' in self.state:
            paginator = self.state['paginator']
            self.state.meta['object_count'] = paginator.count
            self.state.meta['number_of_pages'] = paginator.num_pages
    
    def get_resource_item(self, instance):
        return self.resource.get_list_resource_item(instance)

class CRUDDetailMixin(object):
    def get_object(self):
        raise NotImplementedError
    
    def fork_state(self):
        super(CRUDDetailMixin, self).fork_state()
        self.state.item = self.get_item()
    
    def get_item(self):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return self.resource.get_resource_item(self.object)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        resource_item = self.get_item()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_update_link(resource_item))

class CRUDDeleteView(CRUDDetailMixin, CRUDView):
    view_class = 'delete_confirmation'
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        resource_item = self.get_item()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_delete_link(resource_item))
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete(self.object):
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        resource_item = self.get_resource_item()
        
        form_link = self.get_delete_link(resource_item)
        response_link = form_link.submit()
        
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)

class CRUDDetailView(CRUDDetailMixin, CRUDView):
    view_class = 'change_form'
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        resource_item = self.get_item()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_update_link(resource_item))
    
    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_change(self.object):
            return http.HttpResponseForbidden(_(u"You may not modify that object"))
        
        resource_item = self.get_item()
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_update_link(resource_item, **form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)
    
    post = put
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete(self.object):
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        resource_item = self.get_item()
        form_link = self.get_restul_delete_link(resource_item)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)

