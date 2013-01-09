#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

VERSION = '0.8.0'
LONG_DESC = """
django-hyperadmin is an API driven Admin interface for resources in Django. Resources tend to be anything you can manipulate with a form (including models) and you configure your API resource like you would an Admin Model.
"""

setup(name='django-hyperadmin',
      version=VERSION,
      description="",
      long_description=LONG_DESC,
      classifiers=[
          'Programming Language :: Python',
          'Operating System :: OS Independent',
          'Natural Language :: English',
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
      ],
      keywords='django',
      maintainer = 'Jason Kraus',
      maintainer_email = 'zbyte64@gmail.com',
      url='http://github.com/zbyte64/django-hyperadmin',
      license='New BSD License',
      packages=find_packages(exclude=['tests']),
      test_suite='tests.runtests.runtests',
      tests_require=(
        'pep8==1.3.1',
        'coverage',
        'django',
        'Mock',
        'nose',
        'django-nose',
      ),
      include_package_data = True,
  )
