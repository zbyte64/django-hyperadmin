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
