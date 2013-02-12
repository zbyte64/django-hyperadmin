from django.contrib.auth.models import User
from django.contrib.formtools.wizard.storage import BaseStorage
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
        return 'success'

class TestStorage(BaseStorage):
    _session = dict()
    
    def _get_data(self):
        return self._session[self.prefix]

    def _set_data(self, value):
        print 'set data:', value
        self._session[self.prefix] = value

    data = property(_get_data, _set_data)

class SimpleWizardTestCase(ResourceTestCase):
    def register_resource(self):
        #TODO custom storage for testing
        TestStorage._session = dict()
        self.site.register(TestStorage, SimpleWizard, app_name='wizard', resource_name='adduser')
        return self.site.registry[TestStorage]
    
    def test_email_step(self):
        #start = self.resource.get_link()
        data = {
            'email': 'z@z.com',
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        endpoint = self.resource.endpoints['step_email'].fork(api_request=api_request)
        assert endpoint.link_prototypes
        response = endpoint.generate_api_response(api_request)
        TestStorage._session['wizard_admin_wizard_adduser_resource']['step_data']['_step_statuses']
        self.assertEqual(endpoint.status, 'complete')
        self.assertEqual(response.endpoint.get_url_name(), 'admin_wizard_adduser_step_username')
        
    def test_username_step(self):
        #start = self.resource.get_link()
        data = {
            'username': 'foobar',
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        endpoint = self.resource.endpoints['step_username'].fork(api_request=api_request)
        endpoint.wizard.set_step_status('email', 'complete')
        assert endpoint.link_prototypes
        response = endpoint.generate_api_response(api_request)
        self.assertEqual(endpoint.status, 'complete')
        self.assertEqual(response.endpoint.get_url_name(), 'admin_wizard_adduser_step_password')
        
    def test_password_step(self):
        #start = self.resource.get_link()
        data = {
            'password': 'secret',
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        endpoint = self.resource.endpoints['step_password'].fork(api_request=api_request)
        endpoint.wizard.set_step_status('email', 'complete')
        endpoint.wizard.set_step_status('username', 'complete')
        assert 'email' in TestStorage._session['wizard_admin_wizard_adduser_resource']['step_data']['_step_statuses']
        assert endpoint.link_prototypes
        response = endpoint.generate_api_response(api_request)
        self.assertEqual(endpoint.status, 'complete')
        self.assertEqual(response, 'success')

