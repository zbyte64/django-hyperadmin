=======
Wizards
=======

The Wizard resource is a collection of step endpoints which represent a series of ordered api requests needed to complete a single task. Once a wizard is created in can be included in your urls or registered to a resource site. 


Example::

    from django import forms
    
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
        
        def can_skip(self):
            return True
    
    class GetPassword(FormStep):
        form_class = PasswordForm
    
    class GetAttribute(FormStep):
        form_class = AttributeForm
        
        def can_skip(self):
            return True
    
    class SimpleWizard(Wizard):
        step_definitions = [
            (GetEmail, {'slug':'email'}),
            (GetUsername, {'slug':'username'}),
            (GetPassword, {'slug':'password'}),
        ]
        
        def done(self, submissions):
            return 'success'
    
    wizard = SimpleWizard(app_name='users', resource_adaptor='make_user')
    urlpatterns += patterns('', (r'^', include(wizard.urls)))


A multi-part step allows for multiple steps to be embedded in a single step.

Multi part step example::

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
    
    class ExpandedWizard(Wizard):
        step_definitions = [
            (GetEmail, {'slug':'email'}),
            (GetUsername, {'slug':'username'}),
            (GetPassword, {'slug':'password'}),
            (GetAttributes, {'slug':'attributes'}),
        ]
        
        def done(self, submissions):
            return 'success'

