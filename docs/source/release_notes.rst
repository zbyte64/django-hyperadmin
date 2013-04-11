=============
Release Notes
=============


0.10.0
======

* Added endpoint method, internal_dispatch, for quick internal api calls
* Added `hyperadmin.get_api`
* Added resource slug
* Added signals & events
* Added exception: LinkNotAvailable
* Added HyperadminJSONENcoder
* Added Detail Link, used when user does not have edit permissions
* Preserve requested content type on response
* Standardized CRUD verbage
* Fixed handling of negative primary keys
* Django 1.5 support
* Integrated with django-datataps
* Added Base64 file upload


0.9.1
=====

* Fixed handling of negative primary keys (#2)
* improved order of operations in get link kwargs


0.9.0
=====

* Added `hyperadmin.contrib.apikey` for key based authentication
* Allow endpoints to be directly mounted in urls with global site object
* Added `Wizard` resource for wizard workflows
* URL names are now fully dynamic
* Endpoints may now specify template and context for html rendering
* Added throttling


0.8.2
=====

* Added Generic Inline Support (requires django.contrib.contenttypes)
* Seperated Autoload functionality
* Allow for links to be followed internally
* Simplified setting resource name and appplication_name


0.8.1
=====

* Fixed non integer based urls for models
* Added OPTIONS method
* Autoload ModelAdmin.fieldsets
