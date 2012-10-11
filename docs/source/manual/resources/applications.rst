=====================
Application Resources
=====================

.. automodule:: hyperadmin.resources.applications

------------
SiteResource
------------

API Endpoints
-------------

* "/" lists resources known in the system.
* "/_authentication/" ; PUT/POST to authenticate, DELETE to logout, GET for useful info and login forms. Uses django sessions by default.

-------------------
ApplicationResource
-------------------

API Endpoints
-------------

* "/<appname>/" lists resources belonging to the app
* "/<appname>/<module>/" mount point of crud resource


