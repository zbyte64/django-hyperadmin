from django.core.paginator import Paginator
from django import forms

from hyperadmin import views

from resources import CRUDResource
from links import Link

class UploadForm(forms.Form):
    path = forms.CharField()
    upload = forms.FileField()
    overwrite = forms.BooleanField(required=False)
    
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(UploadForm, self).__init__(**kwargs)
        if self.instance:
            self.initial['path'] = self.instance.path
            self.initial['overwrite'] = True
    
    def save(self, storage):
        if self.cleaned_data.get('overwrite', False): #TODO would be better if storage accepted an argument to overwrite
            if storage.exists(self.cleaned_data['path']):
                storage.delete(self.cleaned_data['path'])
        return storage.save(self.cleaned_data['path'], self.cleaned_data['upload'])

#CONSIDER: post needs to be multipart

class StorageResource(CRUDResource):
    #resource_adaptor = storage object
    paginator = Paginator
    
    #TODO
    list_view = views.StorageListResourceView
    detail_view = views.StorageDetailResourceView
    
    def get_paginator(self, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)
    
    def get_listing(self, request):
        path = request.GET.get('path', '')
        try:
            return self.resource_adaptor.listdir(path)
        except NotImplementedError:
            return [], [] #dirs, files
    
    def get_form_class(self):
        return self.form_class
    
    def get_ln_links(self, instance=None):
        #this will get moved to the resource views
        links = list()
        if hasattr(self.resource_adaptor, 'get_upload_link'):
            links.append(self.resource_adaptor.get_upload_link(instance=instance))
        else:
            form_cls = self.get_form_class()
            if instance:
                form = form_cls(instance=instance)
            else:
                form = form_cls()
            links.append(Link(form=form))
        return links + super(StorageResource, self).get_ln_links(instance=instance)

