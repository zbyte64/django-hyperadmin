import base64

from django import forms
from django.core.files.base import ContentFile
from django.middleware.csrf import get_token

from hyperadmin.resources.storages.endpoints import BoundFile


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

    def add_csrf_field(self, request):
        value = get_token(request)
        self.fields['csrfmiddlewaretoken'] = forms.CharField(initial=value, widget=forms.HiddenInput)

    def save(self, commit=True):
        if self.cleaned_data.get('overwrite', False): #TODO would be better if storage accepted an argument to overwrite
            if self.storage.exists(self.cleaned_data['name']):
                self.storage.delete(self.cleaned_data['name'])
        name = self.storage.save(self.cleaned_data['name'], self.cleaned_data['upload'])
        return BoundFile(self.storage, name)


class Base64UploadForm(UploadForm):
    upload = forms.CharField(widget=forms.Textarea)

    def clean_upload(self):
        django_file = None
        payload = self.cleaned_data.get('upload')
        if payload:
            try:
                django_file = ContentFile(base64.b64decode(payload))
            except TypeError as error:
                raise forms.ValidationError('Inproperly encoded file: %s' % error)
        return django_file


class UploadLinkForm(forms.Form):
    name = forms.CharField() #desired file name
    upload_to = forms.CharField(required=False) #directory path
    overwrite = forms.BooleanField(required=False)

    def __init__(self, **kwargs):
        self.storage = kwargs.pop('storage')
        self.resource = kwargs.pop('resource')
        self.request = kwargs.pop('request') #this is useful because we may return a full url
        super(UploadLinkForm, self).__init__(**kwargs)

    def save(self, commit=True):
        import os
        file_name = self.storage.get_valid_name(self.cleaned_data['name'])
        upload_to = self.cleaned_data.get('upload_to', '')
        if upload_to:
            path = os.path.join(upload_to, file_name)
        else:
            path = file_name
        overwrite = self.cleaned_data.get('overwrite', False)
        if overwrite:
            name = path
        else:
            name = self.storage.get_available_name(path)
        form_kwargs = {'initial':{'name':name, 'overwrite':overwrite}}
        link = self.resource.link_prototypes['create'].get_link(form_kwargs=form_kwargs, rel='direct-upload')
        link.form.add_csrf_field(self.request)
        response_type = self.request.META.get('HTTP_ACCEPT', None)
        if response_type:
            link.state['extra_get_params']['_HTTP_ACCEPT'] = 'text/html-iframe-transport;level=1,'+response_type
        return link
