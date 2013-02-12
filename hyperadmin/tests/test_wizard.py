from django.contrib.auth.models import User
from django import forms

from hyperadmin.tests.test_resources import ResourceTestCase

from hyperadmin.resources.wizard import Wizard, FormStep


class EmailForm(forms.Form):
    email = forms.EmailField()

class UsernameForm(forms.Form):
    username = forms.CharField()

class PasswordForm(forms.Form):
    password = forms.PasswordField()

class GetEmail(FormStep):
    form_class = EmailForm

class GetUsername(FormStep):
    form_class = UsernameForm

class GetPassword(FormStep):
    form_class = PasswordForm

class SimpleWizard(Wizard):
    step_definitions = [
        (GetEmail, {'slug':'email'})
        (GetUsername, {'slug':'username'})
        (GetPassword, {'slug':'password'})
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
        self.site.register(User, SimpleWizard)
        return self.site.registry[User]
    
    def test_email_step(self):
        #start = self.resource.get_link()
        email_e = self.resource.endpoints['step_email'].get_link()
        data = {
            'email': 'z@z.com',
        }
        response = email_e.submit(data=data)
        

