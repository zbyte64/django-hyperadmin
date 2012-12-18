from django.views.generic.detail import SingleObjectMixin

from hyperadmin.resources.crud.endpoints import ListEndpoint as BaseListEndpoint, CreateEndpoint as BaseCreateEndpoint, DetailEndpoint as BaseDetailEndpoint, DeleteEndpoint as BaseDeleteEndpoint


class ModelMixin(object):
    model = None
    queryset = None
    
    def get_queryset(self):
        return self.resource.get_queryset()

class DetailMixin(ModelMixin, SingleObjectMixin):
    def get_object(self):
        if not hasattr(self, 'object'):
            self.object = SingleObjectMixin.get_object(self)
        return self.object

class ListEndpoint(ModelMixin, BaseListEndpoint):
    pass

class CreateEndpoint(ModelMixin, BaseCreateEndpoint):
    pass

class DetailEndpoint(DetailMixin, BaseDetailEndpoint):
    pass

class DeleteEndpoint(DetailMixin, BaseDeleteEndpoint):
    pass


class InlineModelMixin(object):
    def get_common_state_data(self):
        self.common_state['parent'] = self.get_parent_instance()
        print self.common_state
        return super(InlineModelMixin, self).get_common_state_data()
    
    def get_parent_instance(self):
        if not hasattr(self, '_parent_instance'):
            queryset = self.resource.parent.get_queryset()
            self._parent_instance = queryset.get(pk=self.kwargs['pk'])
        return self._parent_instance
    
    def get_queryset(self):
        return self.resource.get_queryset(self.get_parent_instance())
    
    def get_url(self):
        return self.reverse(self.get_url_name(), pk=self.common_state['parent'].pk)

class InlineDetailMixin(InlineModelMixin, SingleObjectMixin):
    def get_object(self):
        queryset = self.get_queryset()
        return queryset.get(pk=self.kwargs['inline_pk'])
    
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
