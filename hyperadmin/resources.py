from django import http

class BaseResource(object):
    def __init__(self, site):
        self.site = site
    
    def get_urls(self):
        return []
    
    def get_embedded_links(self, instance=None):
        return []
    
    def get_outbound_links(self, instance=None):
        #TODO return breadcrumb links
        return []
    
    def get_templated_queries(self):
        return []
    
    def get_instance_url(self, instance):
        return None
    
    def get_items(self):
        return []
    
    def get_form_class(self, instance=None):
        return None
    
    def generate_response(self, view, instance=None, errors=None):
        content_type = view.get_content_type()
        media_type_cls = self.site.media_types.get(content_type, None)
        if media_type_cls is None:
            pass
        media_type = media_type_cls(view)
        return media_type.serialize(view, instance=instance, errors=errors)
    
    def generate_create_response(self, view, instance):
        next_url = self.get_instance_url(instance)
        response = http.HttpResponse(next_url, status=303)
        response['Location'] = next_url
        return response
    
    def generate_delete_response(self, view):
        next_url = ''
        response = http.HttpResponse(next_url, status=303)
        response['Location'] = next_url
        return response

class ModelResource(BaseResource):
    pass
