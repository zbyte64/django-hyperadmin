from django import forms

from hyperadmin.resources.storages.views import BoundFile

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

class UploadLinkForm(forms.Form):
    name = forms.CharField() #desired file name
    upload_to = forms.CharField() #directory path
    overwrite = forms.BooleanField(required=False)
    
    def __init__(self, **kwargs):
        self.storage = kwargs.pop('storage')
        self.resource = kwargs.pop('resource')
        super(UploadLinkForm, self).__init__(**kwargs)
    
    def save(self, commit=True):
        import os
        file_name = self.storage.get_valid_name(self.cleaned_data['name'])
        path = os.path.join(self.cleaned_data['upload_to'], file_name)
        overwrite = self.cleaned_data.get('overwrite', False)
        if overwrite:
            name = path
        else:
            name = self.storage.get_available_name(path)
        form_kwargs = {'initial':{'name':name, 'overwrite':overwrite}}
        link = self.resource.get_create_link(form_kwargs=form_kwargs)
        return link
