#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

VERSION = '0.8.1'
LONG_DESC = open('README.rst', 'r').read()

setup(name='django-hyperadmin',
      version=VERSION,
      description="A hypermedia API framework for Django.",
      long_description=LONG_DESC,
      classifiers=[
          'Programming Language :: Python',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Operating System :: OS Independent',
          'Natural Language :: English',
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
      ],
      keywords='django hypermedia REST',
      author = 'Jason Kraus',
      author_email = 'zbyte64@gmail.com',
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
      install_requires=[
        'mimeparse',
      ],
      include_package_data = True,
      zip_safe = False,
  )
