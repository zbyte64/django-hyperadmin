.. _authentication:

==============
Authentication
==============


API Key
=======

hyperadmin ships with an application to do basic API key authentication.

------------
Installation
------------

Add `hyperadmin.contrib.apikey` to INSTALLED_APPS.

Add the following to your settings::

    DEFAULT_API_REQUEST_CLASS = 'hyperadmin.contrib.apikey.apirequests.HTTPAPIKeyRequest'


