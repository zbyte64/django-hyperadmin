from django import forms

class StepControlForm(forms.Form):
    skip_steps = forms.MultipleChoiceField(choices=[], required=False)
    desired_step = forms.ChoiceField(choices=[], required=False)
    
    def __init__(self, **kwargs):
        available_steps = kwargs.pop('available_steps', [])
        super(StepControlForm, self).__init__(**kwargs)
        self.fields['skip_steps'].choices = available_steps
        self.fields['desired_step'].choices = available_steps

