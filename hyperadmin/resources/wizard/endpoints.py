from hyperadmin.resources import ResourceEndpoint

from hyperadmin.resources.wizard.links import FormStepLinkPrototype, ControlStepLinkPrototype
from hyperadmin.resources.wizard.forms import StepControlForm


class StepList(ResourceEndpoint):
    url_suffix = r'^$'
    name_suffix = 'list'
    link_prototype = ControlStepLinkPrototype
    form_class = StepControlForm
    
    @property
    def wizard(self):
        return self.parent
    
    @property
    def prototype_method_map(self):
        return {
            'GET':'list',
            'POST':'list',
        }
    
    def get_link_prototypes(self):
        return [
            (self.link_prototype, {'name':'list'}),
        ]
    
    #post here for step control
    #get for loader, api for steps as items with status

class StepProvider(object):
    slug = None
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
    
    @property
    def status(self):
        return self.wizard.step_statuses[self.slug]
    
    def get_url_suffix(self):
        return r'^%s/$' % self.slug
    
    def get_name_suffix(self):
        return 'step_%s' % self.slug
    
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
        return super(FormStep, self).get_context_data(**kwargs)
    
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
    
    def form_valid(self, form):
        self.wizard.set_step_data(self.slug, form.cleaned_data)
        self.wizard.set_step_status(self.slug, 'complete')
    
    def form_invalid(self, form):
        pass

