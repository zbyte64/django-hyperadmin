from hyperadmin.links import LinkPrototype


class FormStepLinkPrototype(LinkPrototype):
    def get_link_kwargs(self, **kwargs):
        link_kwargs = {'on_submit':self.handle_submission,
                       'method':'POST',
                       'url':self.get_url(),
                       'form_class': self.get_form_class(),
                       'prompt':'step',
                       'rel':'step',}
        link_kwargs.update(kwargs)
        return super(FormStepLinkPrototype, self).get_link_kwargs(**link_kwargs)
    
    def handle_submission(self, link, submit_kwargs):
        """
        Called when the link is submitted. Returns a link representing the response.
        
        :rtype: Link
        """
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            self.endpoint.form_valid(form)
            
            return self.on_success()
        self.endpoint.form_invalid(form)
        return link.clone(form=form)
    
    def get_next_step_kwargs(self):
        return {
            'skip_steps': self.endpoint.get_skip_steps(),
            'desired_step': self.endpoint.get_desired_step(),
        }
    
    def on_success(self, item=None):
        params = self.get_next_step_kwargs()
        return self.endpoint.wizard.next_step(**params)

class ControlStepLinkPrototype(LinkPrototype):
    def get_link_kwargs(self, **kwargs):
        link_kwargs = {'on_submit':self.handle_submission,
                       'method':'POST',
                       'url':self.get_url(),
                       'form_class': self.get_form_class(),
                       'prompt':'step',
                       'rel':'step',}
        link_kwargs.update(kwargs)
        return super(ControlStepLinkPrototype, self).get_link_kwargs(**link_kwargs)
    
    def handle_submission(self, link, submit_kwargs):
        """
        Called when the link is submitted. Returns a link representing the response.
        
        :rtype: Link
        """
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            return self.on_success(form)
        return link.clone(form=form)
    
    def get_next_step_kwargs(self, form):
        return {
            'skip_steps': form.cleaned_data.get('skip_steps', []),
            'desired_step': form.cleaned_data.get('desired_step', None),
        }
    
    def on_success(self, form):
        params = self.get_next_step_kwargs(form)
        return self.endpoint.wizard.next_step(**params)

