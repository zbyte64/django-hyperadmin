from hyperadmin.endpoints import VirtualEndpont, Endpoint
from hyperadmin.resources import BaseResource, ResourceEndpoint

from hyperadmin.resources.wizard.links import FormStepLinkPrototype


class Wizard(BaseResource):
    step_definitions = [] #tuples of Step and dictionary kwargs, kwarg must contain slug
    
    @property
    def steps(self):
        ret = list()
        for endpoint in self.endpoints.itervalues():
            if isinstance(endpoint, StepProvider):
                ret.append(endpoint)
        return ret
    
    def get_instances(self):
        return self.steps
    
    def get_view_endpoints(self):
        endpoints = super(Wizard, self).get_view_endpoints()
        endpoints.extend(self.step_definitions)
        return endpoints
    
    def update_status(self, slug, status):
        statuses = {
            slug: status
        }
        return self.update_statuses(statuses)
    
    def update_statuses(self, statuses):
        self.state.pop('step_statuses')
        return self.set_step_statuses(statuses)
    
    @property
    def step_statuses(self):
        if 'step_statuses' not in self.state:
            self.state['step_statuses'] = self.get_step_statuses()
        return self.state['step_statuses']
    
    def get_step_statuses(self):
        raise NotImplementedError
    
    def set_step_statuses(self, statuses):
        raise NotImplementedError
    
    def get_next_step(self, skip_steps=[], desired_step=None):
        statuses = {}
            
        for step in self.steps:
            if step.slug in skip_steps and step.can_skip():
                statuses[step.slug] = 'skipped'
            elif step.status == 'incomplete':
                if desired_step and step.slug != desired_step and step.status.can_skip():
                    #CONSIDER: this assumes we can get to our desired step
                    statuses[step.slug] = 'skipped'
                    continue
                self.update_statuses(statuses)
                return step
        self.update_statuses(statuses)
        return None
    
    #post here for step control
    #get for loader, api for steps as items with status

class StepProvider(object):
    slug = None
    status_choices = [
        ('incomplete', 'Incomplete')
        ('inactive', 'Inactive')
        ('skipped', 'Skipped')
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

class Step(StepProvider, ResourceEndpoint):
    pass

class FormStep(Step):
    link_prototype = FormStepLinkPrototype
    form_class = None
    
    @property
    def prototype_method_map(self):
        return {
            'GET':'step_%s' % self.slug,
            'POST':'step_%s' % self.slug,
        }
    
    def get_url_suffix(self):
        return r'^%s/$' % self.slug
    
    def get_name_suffix(self):
        return 'step_%s' % self.slug
    
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
            link = links.add_link('wizard' % self.step_key, link_factor='LN', form_kwargs=form_kwargs, prompt='Skip')
        return links

class MultiPartStep(Wizard, StepProvider):
    #main form is step control from wizard
    
    def get_namespaces(self):
        namespaces = super(MultiPartStep, self).get_namespaces()
        #all our substeps are namespaces
        for endpoint in self.steps:
            namespace = Namespace(name='substep-%s'% endpoint.slug, endpoint=endpoint)
            namespaces[namespace.name] = namespace
        return namespaces
    
    def get_outbound_links(self):
        links = self.create_link_collection()
        #if all steps are optional
        #link that represents continue checkout
        form_kwargs = {
            'initial': {
                'skip_steps': [self.slug],
            },
        }
        link = links.add_link(self, link_factor='LN', form_kwargs=form_kwargs, prompt='Continue')
        return links

