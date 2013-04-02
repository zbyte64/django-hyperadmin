from django.contrib.contenttypes.models import ContentType
from django import forms

from hyperadmin.resources.models.resources import InlineModelResource


class GenericInlineModelResource(InlineModelResource):
    model = None
    ct_field = "content_type"
    ct_fk_field = "object_id"
    
    def post_register(self):
        self._ct_field = self.opts.get_field(self.ct_field)
        self._ct_fk_field = self.opts.get_field(self.ct_fk_field)
        if self.rel_name is None:
            self.rel_name = '-'.join((
                self.opts.app_label, self.opts.object_name.lower(),
                self.ct_field, self.ct_fk_field,
            ))
        super(InlineModelResource, self).post_register()
    
    @property
    def content_type(self):
        return ContentType.objects.get_for_model(self.model)
    
    def get_queryset(self, parent):
        queryset = self.resource_adaptor.objects.all()
        
        queryset = queryset.filter(**{
            self.ct_field: self.content_type,
            self.ct_fk_field: parent.pk,
        })
        
        if not self.has_create_permission():
            queryset = queryset.none()
        return queryset
    
    def get_primary_query(self, **kwargs):
        return self.get_queryset(parent=self.state['parent'].instance)
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        
        resource = self
        
        class AdminForm(forms.ModelForm):
            state = self.state
            
            def save(self, commit=True):
                instance = super(AdminForm, self).save(commit=False)
                
                setattr(instance, resource._ct_field.get_attname(), resource.content_type.pk)
                setattr(instance, resource._ct_fk_field.get_attname(), self.state['parent'].instance.pk)
                if commit:
                    instance.save()
                return instance
            
            class Meta:
                model = self.model
                exclude = self.get_exclude() + [self.ct_field, self.ct_fk_field]
                #TODO formfield overides
                #TODO fields
        return AdminForm
