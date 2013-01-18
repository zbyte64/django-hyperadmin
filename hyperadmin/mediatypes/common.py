from django.core.files import File
from django import http


BUILTIN_MEDIA_TYPES = dict()

class MediaType(object):
    recognized_media_types = []
    
    @classmethod
    def register_with_builtins(cls):
        for media_type in cls.recognized_media_types:
            BUILTIN_MEDIA_TYPES[media_type] = cls
    
    def __init__(self, api_request):
        self.api_request = api_request
    
    @property
    def site(self):
        return self.api_request.get_site()
    
    def get_django_request(self):
        return self.api_request.get_django_request()
    
    #TODO
    def handle_redirect(self, link):
        if self.api_request.method != 'GET':
            response = http.HttpResponse(link.get_absolute_url(), status=303)
            response['Location'] = link.get_absolute_url()
        else:
            response = http.HttpResponseRedirect(link.get_absolute_url())
        return response
    
    def detect_redirect(self, link):
        if link.get_absolute_url() != self.api_request.get_full_path():
            return True
        return False
    
    def serialize(self, content_type, link, state):
        '''
        Return an HttpResponse
        '''
        raise NotImplementedError
    
    def options_serialize(self, content_type, links, state):
        """
        Return an HttpResponse describing the available OPTIONS at an endpoint
        
        :param links: dictionary mapping available HTTP methods to a link
        """
        context = {
            'links':links,
            'content_type':content_type,
            'allow':','.join(links.iterkeys()),
        }
        response = http.HttpResponse()
        response['Allow'] = context['allow']
        return response
    
    def deserialize(self):
        '''
        returns keyword arguments for instantiating a form
        '''
        raise NotImplementedError
    
    def prepare_field_value(self, val):
        if isinstance(val, File):
            if hasattr(val, 'name'):
                val = val.name
            else:
                val = None
        return val
    
    def get_form_instance_values(self, form, include_initial=True):
        data = dict()
        if getattr(form, 'instance', None) or include_initial:
            for name, field in form.fields.iteritems():
                val = form[name].value()
                val = self.prepare_field_value(val)
                data[name] = val
        return data
    
    def get_related_resource_from_field(self, field):
        return self.site.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.site.get_html_type_from_field(field)

