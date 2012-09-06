from django import forms
from django.conf.urls.defaults import patterns, url
from django.utils.functional import update_wrapper

import urllib

from hyperadmin import views
from hyperadmin.views.storages import BoundFile

from resources import CRUDResource
from links import Link

class UploadForm(forms.Form):
    name = forms.CharField()
    upload = forms.FileField()
    overwrite = forms.BooleanField(required=False)
    
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        self.storage = kwargs.pop('storage')
        super(UploadForm, self).__init__(**kwargs)
        if self.instance:
            self.initial['name'] = self.instance.name
            self.initial['overwrite'] = True
    
    def save(self, commit=True):
        if self.cleaned_data.get('overwrite', False): #TODO would be better if storage accepted an argument to overwrite
            if self.storage.exists(self.cleaned_data['name']):
                self.storage.delete(self.cleaned_data['name'])
        name = self.storage.save(self.cleaned_data['name'], self.cleaned_data['upload'])
        return BoundFile(self.storage, name)

#CONSIDER: post needs to be multipart

class StorageResource(CRUDResource):
    #resource_adaptor = storage object
    form_class = UploadForm
    
    list_view = views.StorageListResourceView
    detail_view = views.StorageDetailResourceView
    
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
            url(r'^(?P<path>.+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%s_%s_detail' % (self.app_name, self.resource_name)),
        )
        return urlpatterns
    
    def get_listing(self, request):
        path = request.GET.get('path', '')
        try:
            return self.resource_adaptor.listdir(path)
        except NotImplementedError:
            return [], [] #dirs, files
    
    def get_links_and_items(self, request):
        dirs, files = self.get_listing(request)
        
        items = list()
        for file_name in files:
            items.append(BoundFile(self.resource_adaptor, file_name))
        
        links = list()
        for directory in dirs:
            url = '%s?%s' % (request.path, urllib.urlencode({'path':directory}))
            link = Link(url=url, prompt=u"Directory: %s" % directory, classes=['filter', 'directory'], rel="filter")
            links.append(link)
        return links, items
    
    def get_form_class(self):
        return self.form_class
    
    def get_instance_url(self, instance):
        return self.reverse('%s_%s_detail' % (self.app_name, self.resource_name), path=instance.name)
    
    def get_embedded_links(self, instance=None):
        links = super(StorageResource, self).get_embedded_links(instance=instance)
        if instance:
            link = Link(url=instance.url,
                        prompt='Absolute Url',
                        rel='storage-url',)
            links.append(link)
        return links

