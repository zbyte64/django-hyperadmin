TODOs
=====

Admin Actions
-------------

Admin actions are functions that return a link object. 
If the action is a string then it is assumed to be the function of the resource. The string is mapped as a url and a link object is automatically generated for it. The ``ActionResourceView`` returns a response with the main form being the link object and the post going to the function of the admin.

Unknowns
--------

* inlines
* fieldsets - perhaps this should be configured client side
* custom controls; some fields may need to specify custom front-end logic so there needs to be away to register new controls in the frontend

Inlines: Make it a sub resource. Inline information & templates are slurped in at the top resource but adding another inline would be an ajax call. May add new field type "schema" which nests in a subtemplate.

Link/Form display hints:

* field inline, display result inlined with a field
* module inline, display towards the bottom of the page, group the resources
* page inline, new page but indicate that it is one nested in


Idea: transactional resource creation (documents only).

Other Features
--------------

* changelist
 * search
 * date hierarchy
* form manipulations
 * readonly
 * markup
* logging
* permissions
* admin actions

