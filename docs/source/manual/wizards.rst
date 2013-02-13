=======
Wizards
=======

The Wizard resource in hyperadmin allows for an action to span multiple api requests through a series of step endpoints.

Example::

    from django import forms

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


