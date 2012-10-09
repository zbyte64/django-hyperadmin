import os

from django.conf.urls.defaults import patterns, url
from django.utils.functional import update_wrapper

from hyperadmin.hyperobjects import Link
from hyperadmin.resources.crud.crud import CRUDResource
from hyperadmin.resources.storages import views
from hyperadmin.resources.storages.forms import UploadForm, UploadLinkForm
from hyperadmin.resources.storages.changelist import StorageChangeList, StoragePaginator


class StorageResource(CRUDResource):
    #resource_adaptor = storage object
    changelist_class = StorageChangeList
    paginator_class = StoragePaginator
    form_class = UploadForm
    upload_link_form_class = UploadLinkForm
    
    list_view = views.StorageListView
    add_view = views.StorageCreateView
    upload_link_view = views.StorageUploadLinkView
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
    
    def get_upload_link_form_class(self):
        return self.upload_link_form_class
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.as_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        
        init = self.get_view_kwargs()
        
        # Admin-site-wide views.
        base_name = self.get_base_url_name()
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name='%slist' % base_name),
            url(r'^add/$',
                wrap(self.add_view.as_view(**init)),
                name='%sadd' % base_name),
            url(r'^upload-link/$',
                wrap(self.upload_link_view.as_view(**init)),
                name='%suploadlink' % base_name),
            url(r'^(?P<path>.+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%sdetail' % base_name),
            url(r'^(?P<path>.+)/delete/$',
                wrap(self.delete_view.as_view(**init)),
                name='%sdelete' % base_name),
        )
        return urlpatterns
    
    def get_listing(self, path):
        try:
            dirs, files = self.resource_adaptor.listdir(path)
            if path:
                files = [os.path.join(path, filename) for filename in files]
            return dirs, files
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
    
    def get_upload_link_form_kwargs(self, **kwargs):
        kwargs = self.get_form_kwargs(**kwargs)
        kwargs['resource'] = self
        return kwargs
    
    def get_upload_link(self, form_kwargs=None, **kwargs):
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.get_upload_link_form_kwargs(**form_kwargs)
        
        link_kwargs = {'url':self.get_upload_link_url(),
                       'resource':self,
                       'on_submit':self.handle_upload_link_submission,
                       'method':'POST',
                       'form_kwargs':form_kwargs,
                       'form_class': self.get_upload_link_form_class(),
                       'prompt':'create upload link',
                       'rel':'upload-link',}
        link_kwargs.update(kwargs)
        create_link = Link(**link_kwargs)
        return create_link
    
    def get_upload_link_url(self):
        return self.reverse('%suploadlink' % self.get_base_url_name())
    
    def get_item_url(self, item):
        instance = item.instance
        return self.reverse('%sdetail' % self.get_base_url_name(), path=instance.name)
    
    def get_delete_url(self, item):
        instance = item.instance
        return self.reverse('%sdelete' % self.get_base_url_name(), path=instance.name)
    
    def handle_upload_link_submission(self, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            #presumably this special form returns a link
            upload_link = form.save()
            return upload_link
        return link.clone(form=form)
    
    def get_outbound_links(self):
        links = super(StorageResource, self).get_outbound_links()
        links.append(self.get_upload_link(link_factor='LO'))
        return links
    
    def get_item_storage_link(self, item, **kwargs):
        link_kwargs = {'url':item.instance.url,
                       'resource':self,
                       'prompt':'Absolute Url',
                       'rel':'storage-url',}
        link_kwargs.update(kwargs)
        storage_link = Link(**link_kwargs)
        return storage_link
    
    def get_item_outbound_links(self, item):
        links = super(StorageResource, self).get_item_outbound_links(item)
        links.append(self.get_item_storage_link(item, link_factor='LO'))
        return links
    
    def get_item_prompt(self, item):
        return item.instance.name

