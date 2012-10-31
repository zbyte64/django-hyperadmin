from django.views import generic

from hyperadmin.resources.views import ResourceViewMixin

class ApplicationResourceView(ResourceViewMixin, generic.ListView):
    view_class = 'app_index'
    
    def get(self, request, *args, **kwargs):
        link = self.resource.get_resource_link()
        return self.generate_response(link)

class SiteResourceView(ApplicationResourceView):
    view_class = 'index'

