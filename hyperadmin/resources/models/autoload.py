'''
Maps django model admin entries to model resources.

Usage::

    from hyperadmin.resources.models.autload import DjangoCTModelAdminLoader
    from django.contrib.admin import site as admin_site
    from hyperadmin import site as root_endpoint
    
    loader = DjangoCTModelAdminLoader(root_endpoint, admin_site)
    loader.register_resources()

'''
from django.conf import settings
from django.db import models


class DjangoModelAdminLoader(object):
    '''
    A helper class that maps admin entries from a 
    `django.contrib.admin.site.AdminSite` object to a `RootEndpoint`
    '''
    def __init__(self, root_endpoint, admin_site):
        self.root_endpoint = root_endpoint
        self.admin_site = admin_site
    
    def get_logger(self):
        return self.root_endpoint.get_logger()
    
    def register_resources(self):
        for model, admin_model in self.admin_site._registry.iteritems():
            if not issubclass(model, models.Model):
                continue
            if model in self.root_endpoint.registry:
                continue
            resource_class = self.generate_resource(admin_model)
            try:
                app_name = model._meta.app_label
                resource = self.root_endpoint.register(model, resource_class, app_name=app_name)
                self.register_inlines(admin_model, resource)
            except Exception as error:
                self.get_logger().exception('Could not autoload: %s' % admin_model)
    
    def generate_resource(self, admin_model):
        '''
        When supplied a subclass of `ModelAdmin`
        Returns a ModelResource class with the following options mapped:
        
        * fields
        * fieldsets (flattened to provided fields)
        * exclude
        * paginator
        * list_display
        * list_filter
        * list_select_related (not used)
        * list_per_page
        * list_max_show_all (not used)
        * list_editable (not used)
        * search_fields
        * date_hierarchy (not used)
        * ordering (not used)
        * form_class
        '''
        from django.contrib.admin import ModelAdmin
        if not isinstance(admin_model, ModelAdmin):
            return
        
        from hyperadmin.resources.models import ModelResource
        from django import forms
        if admin_model.fieldsets:
            mfields = list()
            for section, params in admin_model.fieldsets:
                mfields.extend(params['fields'])
        else:
            mfields = admin_model.fields
        class GeneratedModelResource(ModelResource):
            #raw_id_fields = ()
            fields = mfields
            exclude = admin_model.exclude
            #fieldsets = None
            #filter_vertical = ()
            #filter_horizontal = ()
            #radio_fields = {}
            #prepopulated_fields = {}
            #formfield_overrides = {}
            #readonly_fields = ()
            #declared_fieldsets = None
            
            #save_as = False
            #save_on_top = False
            paginator = admin_model.paginator
            inlines = list()
            
            #list display options
            list_display = list(admin_model.list_display)
            #list_display_links = ()
            list_filter = admin_model.list_filter
            list_select_related = admin_model.list_select_related
            list_per_page = admin_model.list_per_page
            list_max_show_all = getattr(admin_model, 'list_max_show_all', 200)
            list_editable = admin_model.list_editable
            search_fields = admin_model.search_fields
            date_hierarchy = admin_model.date_hierarchy
            ordering = admin_model.ordering
            form_class = getattr(admin_model, 'form_class', None)
        
        if 'action_checkbox' in GeneratedModelResource.list_display:
            GeneratedModelResource.list_display.remove('action_checkbox')
        
        if admin_model.form != forms.ModelForm:
            GeneratedModelResource.form_class = admin_model.form
        
        return GeneratedModelResource
    
    def register_inlines(self, admin_model, resource):
        for inline_cls in admin_model.inlines:
            self.register_inline(admin_model, resource, inline_cls)
    
    def register_inline(self, admin_model, resource, inline_cls):
        inline_resource = self.generate_inline(inline_cls)
        if inline_resource:
            try:
                resource.register_inline(inline_resource)
            except:
                self.get_logger().exception('Could not autoload inline: %s' % inline_cls)
            else:
                resource.inlines.append(inline_resource)
                return inline_resource
    
    def generate_inline(self, inline_cls):
        '''
        When supplied a subclass of `InlineModelAdmin`
        Returns an InlineModelResource with the following options mapped:
        
        * model
        * fields
        * exclude
        * fk_name
        '''
        from django.contrib.admin.options import InlineModelAdmin
        
        if not issubclass(inline_cls, InlineModelAdmin):
            return None
        
        from hyperadmin.resources.models import InlineModelResource
        
        class GeneratedInlineModelResource(InlineModelResource):
            model = inline_cls.model
            fields = inline_cls.fields
            exclude = inline_cls.exclude
            fk_name = inline_cls.fk_name
        
        return GeneratedInlineModelResource

class DjangoCTModelAdminLoader(DjangoModelAdminLoader):
    '''
    Extends `DjangoModelAdminLoader` to provide support for autloading 
    generic inlines
    '''
    def generate_inline(self, inline_cls):
        '''
        When supplied a subclass of `GenericInlineModelAdmin`
        Returns a GenericInlineModelResource with the following options mapped:
        
        * model
        * fields
        * exclude
        * ct_field
        * ct_fk_field
        '''
        from django.contrib.contenttypes.generic import GenericInlineModelAdmin
        
        if not issubclass(inline_cls, GenericInlineModelAdmin):
            return super(DjangoCTModelAdminLoader, self).generate_inline(inline_cls)
        
        from hyperadmin.resources.models.generic import GenericInlineModelResource
        
        class GeneratedInlineModelResource(GenericInlineModelResource):
            model = inline_cls.model
            fields = inline_cls.fields
            exclude = inline_cls.exclude
            ct_field = inline_cls.ct_field
            ct_fk_field = inline_cls.ct_fk_field
            formset = inline_cls.formset #TODO is this used?
        
        return GeneratedInlineModelResource

DEFAULT_LOADER = DjangoModelAdminLoader

if 'django.contrib.contenttypes' in settings.INSTALLED_APPS:
    DEFAULT_LOADER = DjangoCTModelAdminLoader
