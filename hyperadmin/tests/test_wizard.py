import django

from hyperadmin.tests.test_resources import ResourceTestCase


class SimpleWizardTestCase(ResourceTestCase):
    def setUp(self):
        if django.VERSION[0] <= 1 and django.VERSION[1] < 4:
            self.skipTest('Wizard requires django 1.4 or later')
        return super(SimpleWizardTestCase, self).setUp()
    
    def register_resource(self):
        from hyperadmin.tests.wizard_fixtures import TestStorage, SimpleWizard
        TestStorage._session = dict()
        self.site.register('mywizard', SimpleWizard, app_name='wizard', resource_name='adduser', storage_class=TestStorage)
        return self.site.registry['mywizard']
    
    def test_get_wizard(self):
        api_request = self.get_api_request()
        resource = self.resource.fork(api_request=api_request)
        resource.get_link()
    
    def test_email_step(self):
        #start = self.resource.get_link()
        data = {
            'email': 'z@z.com',
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        endpoint = self.resource.endpoints['email'].fork(api_request=api_request)
        assert endpoint.link_prototypes
        response = endpoint.generate_api_response(api_request)
        self.assertEqual(endpoint.status, 'complete')
        self.assertEqual(response.endpoint.get_url_name(), 'admin_wizard_adduser_step_username')
        
    def test_username_step(self):
        #start = self.resource.get_link()
        data = {
            'username': 'foobar',
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        endpoint = self.resource.endpoints['username'].fork(api_request=api_request)
        endpoint.wizard.set_step_status('email', 'complete')
        assert endpoint.link_prototypes
        response = endpoint.generate_api_response(api_request)
        self.assertEqual(endpoint.status, 'complete')
        self.assertEqual(response.endpoint.get_url_name(), 'admin_wizard_adduser_step_password')
        
    def test_password_step(self):
        #start = self.resource.get_link()
        data = {
            'password': 'secret',
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        endpoint = self.resource.endpoints['password'].fork(api_request=api_request)
        endpoint.wizard.set_step_status('email', 'complete')
        endpoint.wizard.set_step_status('username', 'complete')
        assert endpoint.link_prototypes
        response = endpoint.generate_api_response(api_request)
        self.assertEqual(endpoint.status, 'complete')
        self.assertEqual(response, 'success')

class ExpandedWizardTestCase(ResourceTestCase):
    def setUp(self):
        if django.VERSION[0] <= 1 and django.VERSION[1] < 4:
            self.skipTest('Wizard requires django 1.4 or later')
        return super(ExpandedWizardTestCase, self).setUp()
    
    def register_resource(self):
        from hyperadmin.tests.wizard_fixtures import TestStorage, ExpandedWizard
        TestStorage._session = dict()
        self.site.register(TestStorage, ExpandedWizard, app_name='wizard', resource_name='adduser')
        return self.site.registry[TestStorage]
        
    def test_get_attributes_step(self):
        #start = self.resource.get_link()
        api_request = self.get_api_request()
        endpoint = self.resource.endpoints['attributes'].fork(api_request=api_request)
        endpoint.wizard.set_step_status('email', 'complete')
        endpoint.wizard.set_step_status('username', 'complete')
        endpoint.wizard.set_step_status('password', 'complete')
        
        link = endpoint.get_link()
        response = link.follow()
    
    def test_attributes_1step(self):
        #start = self.resource.get_link()
        data = {
            'key': 'firstname',
            'value': 'johnson',
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        metastep = self.resource.endpoints['attributes'].fork(api_request=api_request)
        metastep.wizard.set_step_status('email', 'complete')
        metastep.wizard.set_step_status('username', 'complete')
        metastep.wizard.set_step_status('password', 'complete')
        
        endpoint = metastep.endpoints['attr1']
        response = endpoint.generate_api_response(api_request)
        self.assertEqual(endpoint.status, 'complete')
        self.assertEqual(response.endpoint.get_url_name(), 'admin_wizard_adduser_step_attributes_step_attr2')
    
    def test_attributes_completion(self):
        #start = self.resource.get_link()
        data = {
            'key': 'firstname',
            'value': 'johnson',
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        metastep = self.resource.endpoints['attributes'].fork(api_request=api_request)
        metastep.wizard.set_step_status('email', 'complete')
        metastep.wizard.set_step_status('username', 'complete')
        metastep.wizard.set_step_status('password', 'complete')
        metastep.set_step_status('attr1', 'complete')
        
        endpoint = metastep.endpoints['attr2']
        response = endpoint.generate_api_response(api_request)
        self.assertEqual(endpoint.status, 'complete')
        self.assertEqual(response, 'success')
    
    def test_attributes_skip_1step(self):
        #start = self.resource.get_link()
        data = {
            'skip_steps': ['attr1'],
        }
        api_request = self.get_api_request(payload={'data':data}, method='POST')
        metastep = self.resource.endpoints['attributes'].fork(api_request=api_request)
        metastep.wizard.set_step_status('email', 'complete')
        metastep.wizard.set_step_status('username', 'complete')
        metastep.wizard.set_step_status('password', 'complete')
        
        control = metastep.endpoints['start']
        response = control.generate_api_response(api_request)
        endpoint = metastep.endpoints['attr1']
        self.assertEqual(endpoint.status, 'skipped')
        self.assertEqual(response.endpoint.get_url_name(), 'admin_wizard_adduser_step_attributes_step_attr2')

#TODO test step listing

