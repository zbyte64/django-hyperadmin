BUILTIN_MEDIA_TYPES = dict()

class MediaType(object):
    def __init__(self, view):
        self.view = view
        self.request = view.request
    
    def serialize(self, content_type, instance=None, errors=None):
        raise NotImplementedError
    
    def deserialize(self, form_class, instance=None):
        raise NotImplementedError
    
    def get_form_instance_values(self, form, include_initial=True):
        data = dict()
        if getattr(form, 'instance', None) or include_initial:
            for name, field in form.fields.iteritems():
                data[name] = form[name].value()
        return data
    
    def get_related_resource_from_field(self, field):
        return self.view.resource.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.view.resource.get_html_type_from_field(field)
        return 'text'


