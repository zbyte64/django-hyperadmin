from django.contrib.auth.models import User
from django import forms

from hyperadmin.tests.test_resources import ResourceTestCase

from hyperadmin.resources.wizard import Wizard, FormStep


class EmailForm(forms.Form):
    email = forms.EmailField()

class UsernameForm(forms.Form):
    username = forms.CharField()

class PasswordForm(forms.Form):
    password = forms.CharField()

class GetEmail(FormStep):
    form_class = EmailForm

class GetUsername(FormStep):
    form_class = UsernameForm

class GetPassword(FormStep):
    form_class = PasswordForm

class SimpleWizard(Wizard):
    step_definitions = [
        (GetEmail, {'slug':'email'}),
        (GetUsername, {'slug':'username'}),
        (GetPassword, {'slug':'password'}),
    ]
    
    def done(self, submissions):
        '''
        :param submissions: dictionary of slug and cleaned values
        '''
        #retrieve payload
        #create user
        pass

class SimpleWizardTestCase(ResourceTestCase):
    def register_resource(self):
        from django.contrib.formtools.wizard.storage.session import SessionStorage
        self.site.register(SessionStorage, SimpleWizard, app_name='wizard', resource_name='adduser')
        return self.site.registry[SessionStorage]
    
    def test_email_step(self):
        #start = self.resource.get_link()
        data = {
            'email': 'z@z.com',
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        endpoint = self.resource.endpoints['step_email'].fork(api_request=api_request)
        assert endpoint.link_prototypes
        response = endpoint.dispatch_api(api_request)
        #response is GETUsername (shouldn't it be a link?)
        self.assertEqual(endpoint.status, 'complete')
