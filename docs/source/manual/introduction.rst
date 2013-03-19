.. _introduction:

============
Introduction
============

Hyperadmin attempts to be an API framework capable of expressing HATEOAS accross various hypermedia formats.

Links
=====

A link is an available state transition that can be performed over HTTP. Links may also have a form attached to represent the various parameters the user may provide. Links are provided by endpoints and drive Hypermeda as the Engine of Application State. A link may require an HTTP method that is not supported by HTML and it is recommended that an endpoint provide an alternative link to support pure HTML clients.

Serialization
=============

Serialization is done from a form object that is attached to an `Item`. Endpoints translate items from their data store to an appropriate form so the media types do not need to know anything about the data store. This way arbitrary storage backends may be added without modifying the media type implementations. Rather media types concentrate on serializing forms and links.

Endpoints
=========

Endpoints build state and provide links at a given URL. Endpoints may contain child endpoints or implement a class based view to handle an incomming request.

Resources
=========

Resources are a collection of endpoints that describe a particular service.

State
=====

All API requests have a state generated and associated to them. A state contains the items to be represented in the response, filtering params, and other general session and request variables to be shared accross the request cycle.

Root Endpoint
=============

A root endpoint is the top most level of an API. It does not provide links but manages authentication and media type registration.

