from django.core.files import File

BUILTIN_MEDIA_TYPES = dict()

class MediaType(object):
    def __init__(self, view):
        self.view = view
        self.request = view.request
    
    @property
    def resource(self):
        return self.view.resource
    
    @property
    def site(self):
        return self.resource.site
    
    def serialize(self, content_type, instance=None, errors=None):
        raise NotImplementedError
    
    def deserialize(self, form_class, instance=None):
        raise NotImplementedError
    
    def get_form_instance_values(self, form, include_initial=True):
        data = dict()
        if getattr(form, 'instance', None) or include_initial:
            for name, field in form.fields.iteritems():
                val = form[name].value()
                if isinstance(val, File):
                    if hasattr(val, 'name'):
                        val = val.name
                    else:
                        val = None
                data[name] = val
        return data
    
    def get_related_resource_from_field(self, field):
        return self.resource.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.resource.get_html_type_from_field(field)

