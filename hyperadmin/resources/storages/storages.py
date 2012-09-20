from django.conf.urls.defaults import patterns, url
from django.utils.functional import update_wrapper

from hyperadmin.hyperobjects import Link
from hyperadmin.resources.crud.crud import CRUDResource
from hyperadmin.resources.storages import views
from hyperadmin.resources.storages.forms import UploadForm
from hyperadmin.resources.storages.changelist import StorageChangeList, StoragePaginator


class StorageResource(CRUDResource):
    #resource_adaptor = storage object
    changelist_class = StorageChangeList
    paginator_class = StoragePaginator
    form_class = UploadForm
    
    list_view = views.StorageListView
    add_view = views.StorageCreateView
    detail_view = views.StorageDetailView
    delete_view = views.StorageDeleteView
    
    def __init__(self, **kwargs):
        self._app_name = kwargs.pop('app_name', '-storages')
        self._resource_name = kwargs.pop('resource_name')
        super(StorageResource, self).__init__(**kwargs)
    
    def get_app_name(self):
        return self._app_name
    app_name = property(get_app_name)
    
    def get_resource_name(self):
        return self._resource_name
    resource_name = property(get_resource_name)
    
    def get_storage(self):
        return self.resource_adaptor
    storage = property(get_storage)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.as_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        
        init = self.get_view_kwargs()
        
        # Admin-site-wide views.
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name='%s_%s_list' % (self.app_name, self.resource_name)),
            url(r'^add/$',
                wrap(self.add_view.as_view(**init)),
                name='%s_%s_add' % (self.app_name, self.resource_name)),
            url(r'^(?P<path>.+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%s_%s_detail' % (self.app_name, self.resource_name)),
            url(r'^(?P<path>.+)/delete/$',
                wrap(self.delete_view.as_view(**init)),
                name='%s_%s_delete' % (self.app_name, self.resource_name)),
        )
        return urlpatterns
    
    def get_listing(self, path):
        try:
            return self.resource_adaptor.listdir(path)
        except NotImplementedError:
            return [], [] #dirs, files
    
    def get_active_index(self):
        path = self.state.params.get('path', '')
        return self.get_listing(path)
    
    def get_templated_queries(self):
        links = super(StorageResource, self).get_templated_queries()
        if 'links' in self.state:
            links += self.state['links']
        return links
    
    def get_form_kwargs(self, item=None, **kwargs):
        kwargs = super(StorageResource, self).get_form_kwargs(item, **kwargs)
        kwargs['storage'] = self.storage
        return kwargs
    
    def get_item_url(self, item):
        instance = item.instance
        return self.reverse('%s_%s_detail' % (self.app_name, self.resource_name), path=instance.name)
    
    def get_delete_url(self, item):
        instance = item.instance
        return self.reverse('%s_%s_delete' % (self.app_name, self.resource_name), path=instance.name)
    
    def get_item_embedded_links(self, item):
        links = super(StorageResource, self).get_item_embedded_links(item)
        link = Link(url=item.instance.url,
                    resource=self,
                    prompt='Absolute Url',
                    rel='storage-url',)
        links.append(link)
        return links

