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


