from hyperadmin.links import Link, LinkPrototype


class FormStepLinkPrototype(LinkPrototype):
    def get_link_kwargs(self, **kwargs):
        link_kwargs = {'on_submit':self.handle_submission,
                       'method':'POST',
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
            'step_key':self.endpoint.step_key,
            'continue_editing': self.endpoint.get_continue_editing(),
            'skip_to_step': self.endpoint.get_skip_to_step(),
            'skip_steps': self.endpoint.get_skip_steps(),
            'expiration': self.endpoint.get_expiration(),
        }
    
    def on_success(self, item=None):
        step_controller = self.endpoint.process.endpoints['step']
        params = self.get_next_step_kwargs()
        next_step = step_controller.get_next_step(**params)
        if next_step is None: #no more steps, goto confirm checkout
            return self.endpoint.process.endpoints['confirm'].get_link()
        return self.endpoint.process.bound_step(next_step).get_link()
