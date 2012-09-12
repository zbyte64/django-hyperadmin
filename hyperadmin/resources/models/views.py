from django.utils.translation import ugettext as _
from django.views import generic
from django import http

from hyperadmin.models import log_action, DELETION
from hyperadmin.hyperobjects import Link
from hyperadmin.resources.views import ResourceViewMixin

class ModelResourceViewMixin(ResourceViewMixin, generic.edit.ModelFormMixin):
    form_class = None
    model = None
    queryset = None
    
    def get_meta(self):
        return {}
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request)
    
    def get_items(self, **kwargs):
        return self.get_queryset()
    
    def get_items_forms(self, **kwargs):
        return [self.get_form(instance=item) for item in self.get_items()]
    
    def get_form_class(self, instance=None):
        return generic.edit.ModelFormMixin.get_form_class(self)
    
    def get_form_kwargs(self):
        return {}
    
    def get_form(self, **kwargs):
        form_class = self.get_form_class(instance=kwargs.get('instance', None))
        form = form_class(**kwargs)
        return form
    
    #form_valid & form_invalid should not be used
    
    def can_add(self):
        return self.resource.has_add_permission(self.request)
    
    def can_change(self, instance=None):
        return self.resource.has_change_permission(self.request, instance)
    
    def can_delete(self, instance=None):
        return self.resource.has_delete_permission(self.request, instance)

class ModelCreateResourceView(ModelResourceViewMixin, generic.CreateView):
    view_class = 'change_form'
    
    def get_queryset(self):
        return []
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), form_link=self.get_create_link(), meta=self.get_meta())
    
    def get_create_link(self, **form_kwargs):
        form_class = self.get_form_class()
        form_kwargs.update(self.get_form_kwargs())
        form = form_class(**form_kwargs)
        create_link = Link(url=self.request.path,
                           method='POST', #TODO should this be put?
                           form=form,
                           prompt='create',
                           rel='create',)
        return create_link
    
    def post(self, request, *args, **kwargs):
        if not self.can_add():
            return http.HttpResponseForbidden(_(u"You may add an object"))
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_create_link(**form_kwargs)
        return self.resource.generate_create_response(self.get_response_media_type(), self.get_response_type(), form_link=form_link, meta=self.get_meta())
    
    def get_ln_links(self, instance=None):
        create_link = self.get_create_link()
        return [create_link] + super(ModelCreateResourceView, self).get_ln_links(instance)

class ModelListResourceView(ModelCreateResourceView):
    view_class = 'change_list'
    
    def get_meta(self):
        resource_item = self.resource.get_resource_item(None, from_list=True)
        form = resource_item.get_form()
        data = dict()
        data['display_fields'] = list()
        for field in form:
            data['display_fields'].append({'prompt':field.label})
        changelist = self.get_changelist()
        data['object_count'] = changelist.paginator.count
        data['number_of_pages'] = changelist.paginator.num_pages
        return data
    
    def get_changelist(self):
        if not hasattr(self, '_changelist'):
            self._changelist = self.resource.get_changelist(self.request)
        return self._changelist
    
    def get_queryset(self):
        return self.get_changelist().result_list
    
    def get_templated_queries(self):
        links = super(ModelListResourceView, self).get_templated_queries()
        links += self.get_changelist_links()
        return links
    
    def get_changelist_links(self):
        links = self.get_changelist_sort_links()
        links += self.get_changelist_filter_links()
        links += self.get_pagination_links()
        #links.append(self.get_search_link())
        return links
    
    def get_changelist_sort_links(self):
        links = list()
        changelist = self.get_changelist()
        from django.contrib.admin.templatetags.admin_list import result_headers
        for header in result_headers(changelist):
            if header.get("sortable", False):
                prompt = unicode(header["text"])
                classes = ["sortby"]
                if "url" in header:
                    links.append(Link(url=header["url"], prompt=prompt, classes=classes+["primary"], rel="sortby"))
                else:
                    if header["ascending"]:
                        classes.append("ascending")
                    if header["sorted"]:
                        classes.append("sorted")
                    links.append(Link(url=header["url_primary"], prompt=prompt, classes=classes+["primary"], rel="sortby"))
                    links.append(Link(url=header["url_remove"], prompt=prompt, classes=classes+["remove"], rel="sortby"))
                    links.append(Link(url=header["url_toggle"], prompt=prompt, classes=classes+["toggle"], rel="sortby"))
        return links
    
    def get_changelist_filter_links(self):
        links = list()
        changelist = self.get_changelist()
        for spec in changelist.filter_specs:
            choices = spec.choices(changelist)
            for choice in choices:
                classes = ["filter"]
                if choice['selected']:
                    classes.append("selected")
                title = spec.title
                if callable(title):
                    title = title()
                prompt = u"%s: %s" % (title, choice['display'])
                links.append(Link(url=choice['query_string'], prompt=prompt, classes=classes, rel="filter"))
        return links
    
    def get_search_link(self):
        pass
    
    def get_pagination_links(self):
        links = list()
        changelist = self.get_changelist()
        paginator, page_num = changelist.paginator, changelist.page_num
        from django.contrib.admin.templatetags.admin_list import pagination
        from django.contrib.admin.views.main import PAGE_VAR
        ctx = pagination(changelist)
        classes = ["pagination"]
        for page in ctx["page_range"]:
            if page == '.':
                continue
            url = changelist.get_query_string({PAGE_VAR: page})
            links.append(Link(url=url, prompt=u"%s" % page, classes=classes, rel="pagination"))
        if ctx["show_all_url"]:
            links.append(Link(url=ctx["show_all_url"], prompt="show all", classes=classes, rel="pagination"))
        return links
    
    def get_resource_item(self, instance):
        return self.resource.get_resource_item(instance, from_list=True)

class ModelDetailMixin(object):
    def get_items(self, **kwargs):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return [self.object]
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), instance=self.object, meta=self.get_meta())

class ModelDeleteResourceView(ModelDetailMixin, ModelResourceViewMixin, generic.DeleteView):
    view_class = 'delete_confirmation'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete(self.object):
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        with log_action(request.user, self.object, DELETION, request=request):
            self.object.delete()
        
        return self.resource.generate_delete_response(self.get_response_media_type(), self.get_response_type())
    
    def get_li_links(self, instance=None):
        if instance and self.can_delete(instance):
            delete_link = Link(url=self.resource.get_delete_url(instance),
                               rel='delete',
                               prompt='delete',
                               method='POST')
            return [delete_link]
        return []


class ModelDetailResourceView(ModelDetailMixin, ModelResourceViewMixin, generic.UpdateView):
    view_class = 'change_form'
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), instance=self.object, form_link=self.get_update_link(instance=self.object), meta=self.get_meta())
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_change(self.object):
            return http.HttpResponseForbidden(_(u"You may not modify that object"))
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_update_link(instance=self.object, **form_kwargs)
        return self.resource.generate_update_response(self.get_response_media_type(), self.get_response_type(), instance=self.object, form_link=form_link, meta=self.get_meta())
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete(self.object):
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        with log_action(request.user, self.object, DELETION, request=request):
            self.object.delete()
        
        return self.resource.generate_delete_response(self.get_response_media_type(), self.get_response_type())
    
    def get_update_link(self, **form_kwargs):
        form_class = self.get_form_class()
        form_kwargs.update(self.get_form_kwargs())
        form = form_class(**form_kwargs)
        update_link = Link(url=self.request.path,
                           method='POST',
                           form=form,
                           prompt='update',
                           rel='update',)
        return update_link
    
    def get_ln_links(self, instance=None):
        links = super(ModelDetailResourceView, self).get_ln_links(instance)
        assert instance
        if instance and self.can_change(instance):
            update_link = self.get_update_link(instance=instance)
            return [update_link] + links
        return links
    
    def get_li_links(self, instance=None):
        if instance and self.can_delete(instance):
            delete_link = Link(url=self.get_instance_url(instance),
                               rel='delete',
                               prompt='delete',
                               method='DELETE')
            return [delete_link]
        return []
    
    def get_outbound_links(self, instance=None):
        links = super(ModelDetailResourceView, self).get_outbound_links(instance=instance)
        if instance is None:
            detail_link = Link(url=self.resource.get_instance_url(self.object), rel='breadcrumb', prompt=unicode(self.object))
            links.append(detail_link)
        return links

class InlineModelMixin(object):
    def get_changelist_links(self):
        return []
    
    def get_parent(self):
        queryset = self.resource.parent_resource.get_queryset(self.request)
        parent = queryset.get(pk=self.kwargs['pk'])
        return parent
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request, instance=self.get_parent())

class InlineModelCreateResourceView(InlineModelMixin, ModelCreateResourceView):
    pass

class InlineModelListResourceView(InlineModelMixin, ModelListResourceView):
    def get_changelist(self):
        if not hasattr(self, '_changelist'):
            self._changelist = self.resource.get_changelist(self.get_parent(), self.request)
        return self._changelist

class InlineModelDetailMixin(object):
    def get_object(self):
        queryset = self.get_queryset()
        return queryset.get(pk=self.kwargs['inline_pk'])

class InlineModelDeleteResourceView(InlineModelDetailMixin, InlineModelMixin, ModelDeleteResourceView):
    pass

class InlineModelDetailResourceView(InlineModelDetailMixin, InlineModelMixin, ModelDetailResourceView):
    pass

