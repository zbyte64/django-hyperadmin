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
        self.common_state['parent'] = self.get_parent()
        return super(InlineModelMixin, self).get_common_state_data()
    
    def get_parent(self):
        if not hasattr(self, '_parent'):
            queryset = self.resource.parent.get_queryset()
            self._parent = queryset.get(pk=self.kwargs['pk'])
        return self._parent
    
    def get_queryset(self):
        return self.resource.get_queryset(self.get_parent())

class InlineDetailMixin(InlineModelMixin, SingleObjectMixin):
    def get_object(self):
        queryset = self.get_queryset()
        return queryset.get(pk=self.kwargs['inline_pk'])

class InlineListEndpoint(InlineModelMixin, ListEndpoint):
    def get_url(self):
        pk = self.state['parent'].pk
        return super(ListEndpoint, self).get_url(pk=pk)

class InlineCreateEndpoint(InlineModelMixin, CreateEndpoint):
    def get_url(self):
        pk = self.state['parent'].pk
        return super(CreateEndpoint, self).get_url(pk=pk)

class InlineDetailEndpoint(InlineDetailMixin, DetailEndpoint):
    url_suffix = r'^(?P<inline_pk>\w+)/$'
    
    def get_url(self, item):
        pk = self.state['parent'].pk
        return super(DetailEndpoint, self).get_url(pk=pk, inline_pk=item.instance.pk)

class InlineDeleteEndpoint(InlineDetailMixin, DeleteEndpoint):
    url_suffix = r'^(?P<inline_pk>\w+)/delete/$'
    
    def get_url(self, item):
        pk = self.state['parent'].pk
        return super(DeleteEndpoint, self).get_url(pk=pk, inline_pk=item.instance.pk)

