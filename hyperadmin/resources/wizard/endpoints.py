from hyperadmin.resources import ResourceEndpoint

from hyperadmin.resources.wizard.links import FormStepLinkPrototype, ControlStepLinkPrototype
from hyperadmin.resources.wizard.forms import StepControlForm


class StepList(ResourceEndpoint):
    url_suffix = r'^$'
    name_suffix = 'start'
    link_prototype = ControlStepLinkPrototype
    form_class = StepControlForm
    
    @property
    def wizard(self):
        return self.parent
    
    @property
    def prototype_method_map(self):
        return {
            'GET':'steps',
            'POST':'steps',
        }
    
    def get_link_prototypes(self):
        return [
            (self.link_prototype, {'name':'steps'}),
        ]
    
    def get_form_kwargs(self, **kwargs):
        available_steps = list()
        for step in self.wizard.available_steps:
            available_steps.append((step.slug, step.get_prompt()))
        params = {
            'available_steps': available_steps
        }
        params.update(kwargs)
        return super(StepList, self).get_form_kwargs(**params)
    #post here for step control
    #get for loader, api for steps as items with status

class StepProvider(object):
    slug = None
    base_url_name_suffix = 'step'
    status_choices = [
        ('incomplete', 'Incomplete'),
        ('inactive', 'Inactive'),
        ('skipped', 'Skipped'),
        ('complete', 'Complete'),
    ]
    
    @property
    def wizard(self):
        return self.parent
    
    def can_skip(self):
        return False
    
    def is_active(self):
        return True
    
    @property
    def status(self):
        return self.wizard.step_statuses[self.slug]
    
    def is_available(self):
        return self.is_active() and self.status in ('incomplete', 'skipped', 'complete')
    
    def get_extra_status_info(self):
        submitted_data = self.wizard.get_step_data(self.slug)
        return {'submitted_data':submitted_data}
    
    def get_url_suffix(self):
        return r'^%s/$' % self.slug
    
    def get_name_suffix(self):
        return self.slug
    
    def get_prompt(self):
        return self.slug
    
    def get_outbound_links(self):
        links = self.create_link_collection()
        if self.can_skip():
            form_kwargs = {
                'initial': {
                    'skip_steps': [self.slug],
                },
            }
            link = links.add_link(self.wizard, link_factor='LN', form_kwargs=form_kwargs, prompt='Skip')
        return links
    
    def get_item(self):
        return self.get_resource_item(self)
    
    def get_common_state_data(self):
        data = super(StepProvider, self).get_common_state_data()
        data['item'] = self.get_item()
        return data
    
class Step(StepProvider, ResourceEndpoint):
    def get_skip_steps(self):
        return []
    
    def get_desired_step(self):
        return None

class FormStep(Step):
    link_prototype = FormStepLinkPrototype
    form_class = None
    
    @property
    def prototype_method_map(self):
        return {
            'GET':'step_%s' % self.slug,
            'POST':'step_%s' % self.slug,
        }
    
    def get_link_prototypes(self):
        return [
            (self.link_prototype, {'name':'step_%s' % self.slug}),
        ]
    
    def get_context_data(self, **kwargs):
        kwargs['form'] = kwargs['link'].form
        return kwargs
        return super(FormStep, self).get_context_data(**kwargs)
    
    def form_valid(self, form):
        self.wizard.set_step_data(self.slug, form.cleaned_data)
        self.wizard.set_step_status(self.slug, 'complete')
    
    def form_invalid(self, form):
        pass

