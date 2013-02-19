=============
Release Notes
=============

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
