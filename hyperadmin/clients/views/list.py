from django.views.generic import TemplateView

from hyperadmin.clients.views.common import ClientMixin


class MultipleObjectMixin(object):
    context_object_name = None
    
    def get_resource_items(self):
        return self.get_state().get_resource_items()
    
    def get_object_list(self):
        return [ri.instance for ri in self.get_resource_items()]
    
    def get_context_object_name(self):
        """
        Get the name to use for the object.
        """
        if self.context_object_name:
            return self.context_object_name
        else:
            return 'object_list'
    
    def get_context_data(self, **kwargs):
        context = super(MultipleObjectMixin, self).get_context_data(**kwargs)
        context_object_name = self.get_context_object_name()
        context[context_object_name] = self.get_object_list()
        context['resource_items'] = self.get_resource_items()
        return context

class ListView(MultipleObjectMixin, ClientMixin, TemplateView):
    view_classes = ['change_list']
    #TODO option for add params for filters
    
    def get_context_data(self, **kwargs):
        #TODO absorb in index api
        context = super(ListView, self).get_context_data(**kwargs)
        links = self.get_state().get_index_queries()
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
