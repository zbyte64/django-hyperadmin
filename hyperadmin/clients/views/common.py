from django.views.generic import View, TemplateView

from hyperadmin.hyperobjects import patch_global_state
from hyperadmin.mediatypes.passthrough import Passthrough


class ClientMixin(object):
    """
    Contains logic for connecting to an endpoint on the API
    """
    resource = None
    url_name = None
    client_site = None
    
    def get_api_endpoint(self):
        for endpoint in self.resource.get_view_endpoints():
            if endpoint['name'] == self.url_name:
                return endpoint
    
    def get_api_kwargs(self):
        return dict(self.kwargs)
    
    def get_api_args(self):
        return list(self.args)
    
    def get_global_state(self):
        #with media type = pass through
        kwargs = {'media_types': {'*': Passthrough}}
        #patch permissions by setting your own client_site
        if self.client_site is not None:
            kwargs['site'] = self.client_site
        return kwargs
    
    def get_api_response(self):
        if not hasattr(self, '_api_response'):
            endpoint = self.get_api_endpoint()
            patch_params = self.get_global_state()
            #TODO patch_endpoint_state(params={})
            #TODO consider: patching global state should be silod to a particular api site
            with patch_global_state(**patch_params):
                api_args = self.get_api_args()
                api_kwargs = self.get_api_kwargs()
                self._api_response = endpoint['view'](self.request, *api_args, **api_kwargs)
        return self._api_response
    
    def get_state(self):
        return self.get_api_response().state
    
    def get_link(self):
        return self.get_api_response().link
    
    def get_context_data(self, **kwargs):
        context = super(ClientMixin, self).get_context_data(**kwargs)
        context['state'] = self.get_state()
        context['link'] = self.get_link()
        return context

class ListView(ClientMixin, TemplateView):
    view_classes = ['change_list']
    #TODO option for add params for filters
    
    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['resource_items'] = context['state'].get_resource_items()
        context['object_list'] = [ri.instance for ri in context['resource_items']]
        #TODO pagination & links
        self.get_change_list_context_data(context['link'], context['state'], context)
        return context
    
    def get_change_list_context_data(self, link, state, context):
        #TODO absorb in index api
        links = state.get_index_queries()
        context['pagination_links'] = [link for link in links if link.rel == 'pagination']
        filter_links = dict()
        #TODO ignore filter links for params that are set
        for link in links :
            if link.rel == 'filter':
                section = link.cl_headers.get('group', link.prompt)
                filter_links.setdefault(section, [])
                filter_links[section].append(link)
        context['filter_links'] = filter_links
        return context

class DetailView(ClientMixin, TemplateView):
    view_classes = ['change_form']
    
    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['resource_item'] = context['state'].item
        context['object'] = context['resource_item'].instance
        return context

