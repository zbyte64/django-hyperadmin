from django import forms
from django.contrib.formtools.wizard.storage import BaseStorage

from hyperadmin.resources.wizard import Wizard, FormStep, MultiPartStep


class EmailForm(forms.Form):
    email = forms.EmailField()

class UsernameForm(forms.Form):
    username = forms.CharField()

class PasswordForm(forms.Form):
    password = forms.CharField()

class AttributeForm(forms.Form):
    key = forms.CharField()
    value = forms.CharField()

class GetEmail(FormStep):
    form_class = EmailForm

class GetUsername(FormStep):
    form_class = UsernameForm

class GetPassword(FormStep):
    form_class = PasswordForm

class GetAttribute(FormStep):
    form_class = AttributeForm
    
    def can_skip(self):
        return True

class GetAttributes(MultiPartStep):
    step_definitions = [
        (GetAttribute, {'slug':'attr1'}),
        (GetAttribute, {'slug':'attr2'}),
    ]

class SimpleWizard(Wizard):
    step_definitions = [
        (GetEmail, {'slug':'email'}),
        (GetUsername, {'slug':'username'}),
        (GetPassword, {'slug':'password'}),
    ]
    
    def done(self, submissions):
        return 'success'

class ExpandedWizard(Wizard):
    step_definitions = [
        (GetEmail, {'slug':'email'}),
        (GetUsername, {'slug':'username'}),
        (GetPassword, {'slug':'password'}),
        (GetAttributes, {'slug':'attributes'}),
    ]
    
    def done(self, submissions):
        return 'success'

class TestStorage(BaseStorage):
    _session = dict()
    
    def _get_data(self):
        return self._session[self.prefix]

    def _set_data(self, value):
        print 'set data:', value
        self._session[self.prefix] = value

    data = property(_get_data, _set_data)
