from django.views import generic

from common import ResourceViewMixin

class ApplicationResourceView(ResourceViewMixin, generic.ListView):
    view_class = 'app_index'
    
    def get_items(self):
        return self.resource.get_items(self.request)
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self)

class SiteResourceView(ApplicationResourceView):
    view_class = 'index'

