from nose.selector import Selector
from nose.plugins import Plugin

import os
import logging
import sys
import unittest

import django
import django.test
from django.conf import settings

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stdout))

class TestDiscoverySelector(Selector):
    
    def wantDirectory(self, dirname):
        log.debug('Do we want dir: %s' % dirname)
        if 'wizard' in dirname and django.VERSION[0] <= 1 and django.VERSION[1] < 4:
            return False
        
        return super(TestDiscoverySelector, self).wantDirectory(dirname)

    def wantClass(self, cls):
        log.debug('Do we want class: %s (%s)' % (cls, issubclass(cls, django.test.TestCase)))
        return issubclass(cls, unittest.TestCase)

    def wantFile(self, filename):
        log.debug('Do we want file: %s' % filename)
        if 'wizard' in filename and django.VERSION[0] <= 1 and django.VERSION[1] < 4:
            return False
        return filename.endswith('.py')
    
    def wantModule(self, module):
        log.debug('Do we want module: %s' % module)
        parts = module.__name__.split('.')
        if 'wizard' in parts and django.VERSION[0] <= 1 and django.VERSION[1] < 4:
            return False
        
        return super(TestDiscoverySelector, self).wantModule(module)
    
    def wantFunction(self, function):
        log.debug('Do we want function: %s' % function)
        return False

class TestDiscoveryPlugin(Plugin):
    enabled = True

    def configure(self, options, conf):
        pass

    def prepareTestLoader(self, loader):
        loader.selector = TestDiscoverySelector(loader.config)

