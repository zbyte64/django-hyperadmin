from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from hyperadmin.resources.crud.endpoints import ListEndpoint, CreateEndpoint, DetailEndpoint, DeleteEndpoint


class InlineModelMixin(object):
    parent_index_name = 'primary'
    
    def get_parent_index(self):
        if 'parent_index' not in self.state:
            self.state['parent_index'] = self.resource.parent.get_index(self.parent_index_name)
            self.state['parent_index'].populate_state()
        return self.state['parent_index']
    
    def get_common_state_data(self):
        self.common_state['parent'] = self.get_parent_instance()
        return super(InlineModelMixin, self).get_common_state_data()
    
    def get_parent_instance(self):
        if not hasattr(self, '_parent_instance'):
            #todo pick kwargs based on index params
            self._parent_instance = self.get_parent_index().get(pk=self.kwargs['pk'])
        return self._parent_instance
    
    def get_queryset(self):
        return self.resource.get_queryset(self.get_parent_instance())
    
    def get_url(self):
        return self.reverse(self.get_url_name(), pk=self.common_state['parent'].pk)

class InlineDetailMixin(InlineModelMixin):
    def get_object(self):
        if not hasattr(self, 'object'):
            queryset = self.get_queryset()
            try:
                self.object = queryset.get(pk=self.kwargs['inline_pk'])
            except ObjectDoesNotExist as error:
                raise Http404(str(error))
        return self.object
    
    def get_url(self, item):
        return self.reverse(self.get_url_name(), pk=self.common_state['parent'].pk, inline_pk=item.instance.pk)

class InlineListEndpoint(InlineModelMixin, ListEndpoint):
    pass

class InlineCreateEndpoint(InlineModelMixin, CreateEndpoint):
    pass

class InlineDetailEndpoint(InlineDetailMixin, DetailEndpoint):
    url_suffix = r'^(?P<inline_pk>\w+)/$'

class InlineDeleteEndpoint(InlineDetailMixin, DeleteEndpoint):
    url_suffix = r'^(?P<inline_pk>\w+)/delete/$'
