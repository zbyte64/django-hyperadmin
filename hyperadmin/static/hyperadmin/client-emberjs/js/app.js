var App = Em.Application.create({});

App.ApplicationController = Ember.Controller.extend();

App.ApplicationView = Ember.View.extend({
    templateName: 'main'
});

App.Link = Em.Object.extend({
  url: function() {
    var url = this.get('href');
    if (url.charAt(0) != '/') {
        url = App.resourceController.collection.get('url') + url
    }
    return url
  }.property('href').cacheable(),
  emberUrl: function() {
    return '#'+this.get('url');
  }.property('href').cacheable()
})
App.Query = App.Link.extend({})
App.Item = App.Link.extend({
  links: Em.ArrayController.create({})
})
App.Template = App.Link.extend({})
App.Error = Em.Object.extend({})

App.resourceController = Em.ObjectController.create({
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
                this.set('template', App.Template.create(data['template']))
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
      }
    })
  })
});

App.handleResponseError = function(jqXHR, textStatus, errorThrown) {
    if (jqXHR.status == 401) {
        var login_url = jqXHR.getResponseHeader("Location")
        if (login_url) {
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
        'json': 'application/vnd.Collection.next+JSON',
    },
    success: App.resourceController.handleResponse,
    error: App.handleResponseError,
    dataType: "json",
    beforeSend: function(jqXHR, settings) {
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

App.AplicationView = App.ResourceView;

$(function() {
  App.initialize();
  var url = $('body').attr('data-api-endpoint')
  App.resourceController.followLink(url)
});

