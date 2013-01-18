from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from hyperadmin.links import LinkPrototype
from hyperadmin.resources.endpoints import ResourceEndpoint


class ListLinkPrototype(LinkPrototype):
    """
    Resource Item Listing
    """
    def get_link_kwargs(self, **kwargs):
        link_kwargs = {'url':self.get_url(),
                       'prompt':'list',
                       'rel':'list',}
        link_kwargs.update(kwargs)
        return super(ListLinkPrototype, self).get_link_kwargs(**link_kwargs)

class CreateLinkPrototype(LinkPrototype):
    """
    Create Resource Item
    """
    def show_link(self, **kwargs):
        return self.resource.has_add_permission()
    
    def get_link_kwargs(self, **kwargs):
        kwargs = super(CreateLinkPrototype, self).get_link_kwargs(**kwargs)
        
        link_kwargs = {'url':self.get_url(),
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_class': self.get_form_class(),
                       'prompt':'create',
                       'rel':'create',}
        link_kwargs.update(kwargs)
        return super(CreateLinkPrototype, self).get_link_kwargs(**link_kwargs)

#TODO consider: Update vs Detail link
class UpdateLinkPrototype(LinkPrototype):
    """
    Update Resource Item
    """
    def show_link(self, **kwargs):
        return self.resource.has_change_permission(item=kwargs.get('item', None))
    
    def get_link_kwargs(self, **kwargs):
        item = kwargs['item']
        
        kwargs = super(UpdateLinkPrototype, self).get_link_kwargs(**kwargs)
        
        link_kwargs = {'url':self.get_url(item=item),
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'form_class': item.get_form_class(),
                       'prompt':'update',
                       'rel':'update',}
        link_kwargs.update(kwargs)
        return super(UpdateLinkPrototype, self).get_link_kwargs(**link_kwargs)

class DeleteLinkPrototype(LinkPrototype):
    """
    Delete Resource Item
    """
    def show_link(self, **kwargs):
        return self.resource.has_delete_permission(item=kwargs.get('item', None))
    
    def get_link_kwargs(self, **kwargs):
        item = kwargs['item']
        
        kwargs = super(DeleteLinkPrototype, self).get_link_kwargs(**kwargs)
        
        link_kwargs = {'url':self.get_url(item=item),
                       'on_submit':self.handle_submission,
                       'method':'POST',
                       'prompt':'delete',
                       'rel':'delete',}
        link_kwargs.update(kwargs)
        return super(DeleteLinkPrototype, self).get_link_kwargs(**link_kwargs)
    
    def handle_submission(self, link, submit_kwargs):
        instance = self.resource.state.item.instance
        instance.delete()
        return self.on_success()

class IndexMixin(object):
    index_name = 'primary'
    
    def get_index(self):
        if self.api_request:
            if 'index' not in self.state:
                self.state['index'] = self.resource.get_index(self.index_name)
                self.state['index'].populate_state()
            return self.state['index']
        else:
            return self.resource.get_index(self.index_name)

class ListEndpoint(IndexMixin, ResourceEndpoint):
    endpoint_class = 'change_list'
    name_suffix = 'list'
    url_suffix = r'^$'
    
    prototype_method_map = {
        'GET': 'list',
        'POST': 'rest-create',
    }
    
    list_prototype = ListLinkPrototype
    create_prototype = CreateLinkPrototype
    
    def get_link_prototypes(self):
        return [
            (self.list_prototype, {'name':'list'}),
            (self.create_prototype, {'name':'rest-create'}),
        ]
    
    def get_outbound_links(self):
        links = self.create_link_collection()
        links.add_link('create', link_factor='LO')
        return links
    
    def get_filter_links(self):
        links = self.create_link_collection()
        index = self.get_index()
        links.extend(index.get_filter_links(rel='filter'))
        return links
    
    def get_pagination_links(self):
        links = self.create_link_collection()
        index = self.get_index()
        links.extend(index.get_pagination_links(rel='paginate'))
        return links
    
    def get_instances(self):
        #CONSIDER view currently determines this
        index = self.get_index()
        page = index.get_page()
        return page.object_list
    
    def get_resource_item(self, instance, **kwargs):
        kwargs.setdefault('endpoint', self)
        return self.resource.get_list_resource_item(instance, **kwargs)
    
    def get_meta(self):
        resource_item = self.resource.get_list_resource_item(instance=None)
        form = resource_item.get_form()
        data = dict()
        data['display_fields'] = list()
        for field in form:
            data['display_fields'].append({'prompt':field.label})
        return data
    
    def get_common_state_data(self):
        data = super(ListEndpoint, self).get_common_state_data()
        
        index = self.get_index()
        paginator = index.get_paginator()
        data['paginator'] = paginator
        data['index'] = index
        self.state.meta['object_count'] = paginator.count
        self.state.meta['number_of_pages'] = paginator.num_pages
        return data

class CreateEndpoint(ResourceEndpoint):
    endpoint_class = 'change_form'
    endpoint_classes = ['add_form']
    name_suffix = 'add'
    url_suffix = r'^add/$'
    
    prototype_method_map = {
        'GET': 'create',
        'POST': 'create',
    }
    
    create_prototype = CreateLinkPrototype
    
    def get_link_prototypes(self):
        return [
            (self.create_prototype, {'name':'create'}),
        ]
    
    def get_breadcrumbs(self):
        breadcrumbs = super(CreateEndpoint, self).get_breadcrumbs()
        breadcrumbs.add_link('create', rel='breadcrumb', link_factor='LO')
        return breadcrumbs
    
    def get_resource_items(self):
        return []

class DetailMixin(IndexMixin):
    url_param_map = {}
    
    def get_object(self):
        if not hasattr(self, 'object'):
            try:
                self.object = self.get_index().get(**self.kwargs)
            except ObjectDoesNotExist as error:
                raise Http404(str(error))
        return self.object
    
    def get_item(self):
        return self.get_resource_item(self.get_object())
    
    def get_common_state_data(self):
        data = super(DetailMixin, self).get_common_state_data()
        data['item'] = self.get_item()
        return data
    
    def get_url_param_map(self):
        return dict(self.url_param_map)
    
    def get_url_params_from_item(self, item):
        param_map = self.get_url_param_map()
        return self.get_index().get_url_params_from_item(item, param_map)
    
    def get_url_suffix(self):
        param_map = self.get_url_param_map()
        url_suffix = '/'.join(self.get_index().get_url_params(param_map))
        url_suffix = '^%s%s' % (url_suffix, self.url_suffix)
        return url_suffix
    
    def get_url(self, item):
        params = self.get_url_params_from_item(item)
        return super(DetailMixin, self).get_url(**params)

class DetailEndpoint(DetailMixin, ResourceEndpoint):
    endpoint_class = 'change_form'
    name_suffix = 'detail'
    url_suffix = r'/$'
    
    prototype_method_map = {
        'GET': 'update',
        'POST': 'update',
        'PUT': 'rest-update',
        'DELETE': 'rest-delete',
    }
    
    update_prototype = UpdateLinkPrototype
    delete_prototype = DeleteLinkPrototype
    
    def get_link_prototypes(self):
        return [
            (self.update_prototype, {'name':'update'}),
            (self.update_prototype, {'name':'rest-update', 'link_kwargs':{'method':'PUT'}}),
            (self.delete_prototype, {'name':'rest-delete', 'link_kwargs':{'method':'DELETE'}}),
        ]
    
    def get_item_outbound_links(self, item):
        links = self.create_link_collection()
        links.add_link('delete', item=item, link_factor='LO')
        return links
    
    def get_breadcrumbs(self):
        breadcrumbs = super(DetailEndpoint, self).get_breadcrumbs()
        breadcrumbs.add_link('update', item=self.common_state.item, rel='breadcrumb', link_factor='LO')
        return breadcrumbs

class DeleteEndpoint(DetailMixin, ResourceEndpoint):
    endpoint_class = 'delete_confirmation'
    name_suffix = 'delete'
    url_suffix = r'/delete/$'
    
    prototype_method_map = {
        'GET': 'delete',
        'POST': 'delete',
    }
    
    delete_prototype = DeleteLinkPrototype
    
    def get_link_prototypes(self):
        return [
            (self.delete_prototype, {'name':'delete'}),
        ]
    
    def get_breadcrumbs(self):
        breadcrumbs = super(DeleteEndpoint, self).get_breadcrumbs()
        breadcrumbs.add_link('update', item=self.common_state.item, rel='breadcrumb', link_factor='LO')
        breadcrumbs.add_link('delete', item=self.common_state.item, rel='breadcrumb', link_factor='LO')
        return breadcrumbs
