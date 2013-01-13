from hyperadmin.resources.crud.endpoints import ListEndpoint, CreateEndpoint, DetailMixin, DetailEndpoint, DeleteEndpoint


class InlineModelMixin(object):
    parent_index_name = 'primary'
    parent_url_param_map = {}
    
    def get_parent_index(self):
        if not self.api_request:
            return self.resource.parent.get_index(self.parent_index_name)
        if 'parent_index' not in self.state:
            self.state['parent_index'] = self.resource.parent.get_index(self.parent_index_name)
            self.state['parent_index'].populate_state()
        return self.state['parent_index']
    
    def get_parent_url_param_map(self):
        return dict(self.parent_url_param_map)
    
    def get_url_suffix_parts(self):
        param_map = self.get_parent_url_param_map()
        parts = self.get_parent_index().get_url_params(param_map)
        parts.append(self.resource.rel_name)
        return parts
    
    def get_url_suffix(self):
        #CONSIDER: the parent endpoint is both a resource and a detail endpoint of another resource
        #if we roll the url then we should lookup the details from the parent endpoint/resource
        parts = self.get_url_suffix_parts()
        url_suffix = '/'.join(parts)
        url_suffix = '^%s%s' % (url_suffix, self.url_suffix)
        return url_suffix
    
    def get_common_state_data(self):
        self.common_state['parent'] = self.get_parent_item()
        return super(InlineModelMixin, self).get_common_state_data()
    
    def get_parent_instance(self):
        if 'parent' in self.state:
            return self.state['parent'].instance
        assert 'parent' not in self.common_state, 'state must inherit from common_state: %r\n%r' % (self.state, self.common_state)
        return self.get_parent_index().get(pk=self.kwargs['pk'])
    
    def get_parent_item(self):
        return self.resource.parent.get_resource_item(self.get_parent_instance())
    
    def get_url_params_from_parent(self, item):
        param_map = self.get_parent_url_param_map()
        return self.get_parent_index().get_url_params_from_item(item, param_map)
    
    def get_url(self):
        item = self.get_parent_item()
        params = self.get_url_params_from_parent(item)
        return self.reverse(self.get_url_name(), **params)

class InlineDetailMixin(InlineModelMixin, DetailMixin):
    url_param_map = {'pk':'inline_pk'}
    
    #TODO get_item includes parent in resource item
    #TODO inline index
    
    def get_url_suffix_parts(self):
        parts = InlineModelMixin.get_url_suffix_parts(self)
        param_map = self.get_url_param_map()
        parts.extend(self.get_index().get_url_params(param_map))
        return parts
    
    def get_url(self, item):
        parent_item = self.get_parent_item()
        params = self.get_url_params_from_parent(parent_item)
        params.update(self.get_url_params_from_item(item))
        return self.reverse(self.get_url_name(), **params)

class InlineListEndpoint(InlineModelMixin, ListEndpoint):
    url_suffix = r'/$'

class InlineCreateEndpoint(InlineModelMixin, CreateEndpoint):
    url_suffix = r'/add/$'

class InlineDetailEndpoint(InlineDetailMixin, DetailEndpoint):
    pass

class InlineDeleteEndpoint(InlineDetailMixin, DeleteEndpoint):
    pass

