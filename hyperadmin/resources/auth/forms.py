from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login

class AuthenticationResourceForm(AuthenticationForm):
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(AuthenticationResourceForm, self).__init__(**kwargs)
    
    def check_for_test_cookie(self):
        return
    
    def save(self, commit=True):
        assert self.request
       
        user = self.get_user()
        login(self.request, user)
        return user

