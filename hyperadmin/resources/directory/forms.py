from django import forms
from django.utils.encoding import force_unicode


class ViewResourceForm(forms.Form):
    display = ['resource_class', 'app_name', 'resource_name']
    
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(ViewResourceForm, self).__init__(**kwargs)
        if self.instance:
            for display in self.display:
                label = display
                self.fields[display] = forms.CharField(label=label)
                if hasattr(self.instance, display):
                    try:
                        val = getattr(self.instance, display)
                    except:
                        val = ''
                else:
                    val = '' #TODO raise ImproperlyConfigured
                if callable(val):
                    try:
                        val = val()
                    except:
                        val = ''
                self.initial[display] = force_unicode(val)
        else:
            pass
