var App = Em.Application.create({});

App.ApplicationController = Ember.Controller.extend();

//here we define our data objects
App.CommonObject = Em.Object.extend({
  css_class: function() {
    var classes = this.get('classes');
    if (classes) {
      return classes.join(' ');
    }
    return '';
  }.property('classes')
});
App.Link = App.CommonObject.extend({
  url: function() {
    var url = this.get('href');
    if (url.charAt(0) != '/') {
        url = App.resourceController.collection.get('url') + url
    }
    return url
  }.property('href'),
  apiUrl: function() {
    var apiUrl = this.get('url')
    var base_url = App.resourceController.get('apiUrl')
    if (apiUrl.indexOf(base_url) == 0) {
        apiUrl = apiUrl.substr(base_url.length)
    }
    return apiUrl
  }.property('href'),
  emberUrl: function() {
    return '#'+this.get('apiUrl');
  }.property('href'),
  isBreadcrumb: function() {
    return this.get('rel') == 'breadcrumb';
  }.property('rel'),
  isSortby: function() {
    return this.get('rel') == 'sortby';
  }.property('rel'),
  isFilterby: function() {
    return this.get('rel') == 'filterby';
  }.property('rel')
})
App.Query = App.Link.extend({})
App.Item = App.Link.extend({
  links: Em.ArrayController.create({})
})
App.Field = App.CommonObject.extend({})
App.Template = App.Link.extend({
  //TODO extend create
})
App.Error = Em.Object.extend({})

//define a controller for managing these data objects
//views bind to this and are automatically updated when the controller issues update actions
App.resourceController = Em.ObjectController.create({
    apiUrl: null,
    collection: Em.ObjectController.create({ //bind data to this
        version: null,
        href: null,
        url: function() {
            var url = this.get('href');
            var end_pos = url.indexOf('?')
            if (end_pos > -1) {
                url = url.substr(0, end_pos)
            }
            return url
        }.property('href'),
        links: Em.ArrayController.create({
            handleResponse: function(data) {
                this.set('content', []);
                for (var i=0; i<data.length; i++) {
                    var link_data = data[i];
                    var link = App.Query.create(link_data);
                    this.pushObject(link);
                }
            }
        }),
        items: Em.ArrayController.create({
            handleResponse: function(data) {
                this.set('content', []);
                for (var i=0; i<data.length; i++) {
                    var item_data = data[i];
                    var item = App.Item.create(item_data);
                    item.set('links', Em.ArrayController.create({
                        content: []
                    }))
                    for (var j=0; j<item_data.links.length; j++) {
                        var link = App.Link.create(item_data.links[j])
                        item.links.pushObject(link)
                    }
                    this.pushObject(item);
                }
            }
        }),
        queries: Em.ArrayController.create({
            handleResponse: function(data) {
                this.set('content', []);
                for (var i=0; i<data.length; i++) {
                    var query_data = data[i];
                    var query = App.Query.create(query_data);
                    this.pushObject(query);
                }
            }
        }),
        template: null,
        error: null,
        handleResponse: function(data) {
            this.set('version', data['version']);
            this.set('href', data['href']);
            this.links.handleResponse(data['links'])
            this.items.handleResponse(data['items'])
            this.queries.handleResponse(data['queries'])
            if (data['template']) {
                var template = App.Template.create(data['template'])
                template.set('data', Em.ArrayController.create({
                    content: []
                }))
                for (var i=0; i<data['template']['data'].length; i++) {
                    var field = App.Field.create(data['template']['data'][i])
                    template.data.pushObject(field)
                }
                this.set('template', template)
            } else {
                this.set('template', null)
            }
            if (data['error']) {
                this.set('error', App.Error.create(data['error']))
            } else {
                this.set('error', null)
            }
        }
    }), 
    followLink: function(url) {
        var settings = $.extend({}, App.requestDefaults, {
            url: url,
            success: this.handleResponse
        })
        $.ajax(settings)
    },
    submitForm: function(form) {
        var settings = $.extend({}, App.requestDefaults, {
            url: form.attr('target'),
            type: form.attr('method') || 'POST',
            data: form.serialize(),
            success: this.handleResponse
        })
        $.ajax(settings)
    },
    handleResponse: function(data, textStatus, jqXHR) {
        App.resourceController.collection.handleResponse(data['collection'])
    }
});

App.updateResourcePath = function() {
    //updates the location to match our current resource controller state
    var url = App.resourceController.collection.get('href')
    var base_url = App.resourceController.get('apiUrl')
    if (url.indexOf(base_url) == 0) {
        url = url.substr(base_url.length)
    }
    App.router.location.setURL(url)
}

//when href changes, call our observer function to update the path
App.resourceController.collection.addObserver('href', App, 'updateResourcePath')

App.Router = Em.Router.extend({
  location: 'hash',
  root: Em.Route.extend({
    index: Em.Route.extend({
      route: '/',
      connectOutlets: function(router) {
        router.get('applicationController').connectOutlet('Resource');
      },
      followLink: function(router, event) {
        var view = event.view
        var url = view.bindingContext.get('url')
        App.resourceController.followLink(url)
      },
      submitForm: function(router, event) {
        var view = event.view
        var form = view.$().find('form');
        App.resourceController.submitForm(form)
      },
      deserialize: function(router, params) {
        //since there are no states, this only gets called once and that is to interpret the initial #url
        //console.log('deserialize', router, params)
        var hash = router.location.location.hash
        var url = App.resourceController.get('apiUrl')
        if (hash) {
            url = url + hash.substr(1);
        }
        //console.log('deserialized', url)
        App.resourceController.followLink(url)
        //location.setURL(path);
        //params = {resource_url: url}
        //return params
      }
    })
  })
});

App.handleResponseError = function(jqXHR, textStatus, errorThrown) {
    if (jqXHR.status == 401) {
        var login_url = jqXHR.getResponseHeader("Location")
        if (login_url) {
            //TODO preserve previous url so we are redirected on login success
            App.resourceController.followLink(login_url)
        } else {
            console.log([jqXHR, textStatus, errorThrown])
        }
    } else {
        console.log([jqXHR, textStatus, errorThrown])
    }
}

App.requestDefaults = {
    accepts: {
        'json': 'application/vnd.Collection.hyperadmin+JSON', //custom media type defintion
    },
    success: App.resourceController.handleResponse,
    error: App.handleResponseError,
    dataType: "json",
    beforeSend: function(jqXHR, settings) { //inject csrf token
        jQuery(document).ajaxSend(function(event, xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            function safeMethod(method) {
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            }
            
            if (!safeMethod(settings.type) && !settings.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        });
    }
}

//emberjs first loads ApplicationView
App.ApplicationView = Em.View.extend({
  templateName: 'main'
});

App.AdminView = Em.View.extend({})

App.ResourceView = App.AdminView.extend({
  templateName: 'resource',
  classNames: ['resource']
})

App.BreadcrumbsView = App.AdminView.extend({
  templateName: 'breadcrumbs',
  classNames: ['breadcrumbs']
})

App.QueriesView = App.AdminView.extend({
  templateName: 'queries',
  classNames: ['queries']
})

App.ErrorView = App.AdminView.extend({
  templateName: 'error',
  classNames: ['error']
})

App.ItemsView = App.AdminView.extend({
  templateName: 'items',
  classNames: ['items']
})

App.TemplateView = App.AdminView.extend({
  templateName: 'template',
  classNames: ['template']
})

App.LinkView = App.AdminView.extend({
  templateName: 'link',
  classNames: ['link']
})

App.BreadcrumbView = App.LinkView.extend({})

App.FormView = App.AdminView.extend({
  templateName: 'form',
  classNames: ['form']
})

$(function() {
  var url = $('body').attr('data-api-endpoint')
  App.resourceController.set('apiUrl', url)
  App.initialize();
});

