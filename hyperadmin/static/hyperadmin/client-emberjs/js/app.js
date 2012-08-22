var App = Em.Application.create();

App.handleResponse = function(data, textStatus, jqXHR) {
    var view_cls = App.ResourceView
    var view = view_cls.create(data)
    $('#container').empty()
    view.appendTo('#container')
}

App.handleResponseError = function(jqXHR, textStatus, errorThrown) {
    if (jqXHR.status == 401) {
        var login_url = jqXHR.getResponseHeader("Location")
        if (login_url) {
            App.followLink(login_url)
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
    success: App.handleResponse,
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

App.followLink = function(url) {
    var settings = $.extend({}, App.requestDefaults, {url: url})
    $.ajax(settings)
}

App.init_application = function() {
  var url = $('body').attr('data-api-endpoint')
  var settings = $.extend({}, App.requestDefaults, {url: url})
  $.ajax(settings)
}

App.AdminView = Em.View.extend({
    followLink: function(event) {
        var view = event.view
        var url = view.bindingContext.href
        App.followLink(url)
    },
    submitForm: function(event) {
        var view = event.view
        var $form = view.$().find('form');
        var settings = $.extend({}, App.requestDefaults, {
            url: $form.attr('target'),
            type: $form.attr('method') || 'POST',
            data: $form.serialize()
        })
        $.ajax(settings)
    }
})

App.LoadingView = App.AdminView.extend({

});

App.ResourceView = App.AdminView.extend({
  templateName: 'resource'
})

App.BreadcrumbsView = App.AdminView.extend({
  templateName: 'breadcrumbs'
})

App.QueriesView = App.AdminView.extend({
  templateName: 'queries'
})

App.ErrorView = App.AdminView.extend({
  templateName: 'error'
})

App.ItemsView = App.AdminView.extend({
  templateName: 'items'
})

App.TemplateView = App.AdminView.extend({
  templateName: 'template'
})

App.LinkView = App.AdminView.extend({
  templateName: 'link'
})

App.BreadcrumbView = App.LinkView.extend({

})

App.FormView = App.AdminView.extend({
  templateName: 'form'
})

