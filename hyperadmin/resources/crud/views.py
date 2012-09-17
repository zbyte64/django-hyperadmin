from hyperadmin.resources.views import ResourceViewMixin


class CRUDResourceViewMixin(ResourceViewMixin):
    form_class = None
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        return self.resource.get_form_class()
    
    def get_form_kwargs(self):
        return {}
    
    def can_add(self):
        return self.resource.has_add_permission(self.request.user)
    
    def can_change(self, instance=None):
        return self.resource.has_change_permission(self.request.user, instance)
    
    def can_delete(self, instance=None):
        return self.resource.has_delete_permission(self.request.user, instance)
    
    def get_create_link(self, **form_kwargs):
        form_class = self.get_form_class()
        form_kwargs.update(self.get_form_kwargs())
        return self.resource.get_create_link(form_class=form_class, form_kwargs=form_kwargs)
    
    def get_restful_create_link(self, **form_kwargs):
        form_class = self.get_form_class()
        form_kwargs.update(self.get_form_kwargs())
        return self.resource.get_restful_create_link(form_class=form_class, form_kwargs=form_kwargs)
    
    def get_update_link(self, item, **form_kwargs):
        form_class = self.get_form_class()
        form_kwargs.update(self.get_form_kwargs())
        return self.resource.get_update_link(item=item, form_class=form_class, form_kwargs=form_kwargs)
    
    def get_delete_link(self, item, **form_kwargs):
        return self.resource.get_delete_link(item=item, form_kwargs=form_kwargs)
    
    def get_restful_delete_link(self, item, **form_kwargs):
        return self.resource.get_restful_delete_link(item=item, form_kwargs=form_kwargs)
    
    def get_list_link(self):
        return self.resource.get_resource_link()

