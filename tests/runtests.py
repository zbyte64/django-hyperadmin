"""
Test support harness for doing setup.py test.
See http://ericholscher.com/blog/2009/jun/29/enable-setuppy-test-your-django-apps/.
"""
import sys

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'

# Bootstrap Django's settings.
from django.conf import settings
settings.DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory;'}
}
settings.TEST_RUNNER = "django_nose.NoseTestSuiteRunner"

def runtests():
    """Test runner for setup.py test."""
    # Run you some tests.
    import django.test.utils
    runner_class = django.test.utils.get_runner(settings)
    test_runner = runner_class(verbosity=1, interactive=True)
    failures = test_runner.run_tests(['hyperadmin'])

    # Okay, so this is a nasty hack. If this isn't here, `setup.py test` craps out
    # when generating a coverage report via Nose. I have no idea why, or what's
    # supposed to be going on here, but this seems to fix the problem, and I
    # *really* want coverage, so, unless someone can tell me *why* I shouldn't
    # do this, I'm going to just whistle innocently and keep on doing this.
    sys.exitfunc = lambda: 0

    sys.exit(failures)
