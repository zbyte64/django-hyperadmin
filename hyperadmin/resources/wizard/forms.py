from django import forms

class StepControlForm(forms.Form):
    skip_steps = forms.MultipleChoiceField(choices=[], required=False)
    desired_step = forms.ChoiceField(choices=[], required=False)
    
    def __init__(self, **kwargs):
        available_steps = kwargs.pop('available_steps', [])
        super(StepControlForm, self).__init__(**kwargs)
        self.fields['skip_steps'].choices = available_steps
        self.fields['desired_step'].choices = available_steps

class StepStatusForm(forms.Form):
    slug = forms.CharField()
    status = forms.CharField()
    can_skip = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False)
    
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(StepStatusForm, self).__init__(**kwargs)
        if self.instance:
            self.initial['slug'] = self.instance.slug
            self.initial['status'] = self.instance.status
            self.initial['can_skip'] = self.instance.can_skip()
            self.initial['is_active'] = self.instance.is_active()
            
            for key, datum in self.instance.get_extra_status_info().iteritems():
                self.fields[key] = forms.CharField(required=False)
                self.initial[key] = datum
