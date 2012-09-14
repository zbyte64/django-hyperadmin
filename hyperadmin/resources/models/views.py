from django.utils.translation import ugettext as _
from django.views import generic
from django import http

from hyperadmin.hyperobjects import Link
from hyperadmin.resources.views import CRUDResourceViewMixin

class ModelResourceViewMixin(CRUDResourceViewMixin):
    model = None
    queryset = None
    
    def get_queryset(self, filter_params=None):
        return self.resource.get_queryset(self.request.user)
    
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

class ModelCreateResourceView(ModelResourceViewMixin, generic.CreateView):
    view_class = 'change_form'
    
    def get_queryset(self):
        return []
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_create_link(), meta=self.get_meta())
    
    def post(self, request, *args, **kwargs):
        if not self.can_add():
            return http.HttpResponseForbidden(_(u"You may add an object"))
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_create_link(**form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, meta=self.get_meta())

class ModelListResourceView(ModelCreateResourceView):
    view_class = 'change_list'
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_restful_create_link(), meta=self.get_meta())
    
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
            self._changelist = self.resource.get_changelist(self.request.user, filter_params=self.request.GET)
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
    
    def get_resource_item(self):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return self.resource.get_resource_item(self.object)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        resource_item = self.get_resource_item()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_update_link(resource_item), meta=self.get_meta())

class ModelDeleteResourceView(ModelDetailMixin, ModelResourceViewMixin, generic.DeleteView):
    view_class = 'delete_confirmation'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete(self.object):
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        resource_item = self.get_resource_item()
        
        form_link = self.get_delete_link(resource_item)
        response_link = form_link.submit()
        
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)

class ModelDetailResourceView(ModelDetailMixin, ModelResourceViewMixin, generic.UpdateView):
    view_class = 'change_form'
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        resource_item = self.get_resource_item()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), self.get_update_link(resource_item), meta=self.get_meta())
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_change(self.object):
            return http.HttpResponseForbidden(_(u"You may not modify that object"))
        
        resource_item = self.get_resource_item()
        form_kwargs = self.get_request_form_kwargs()
        form_link = self.get_update_link(resource_item, **form_kwargs)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link, meta=self.get_meta())
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete(self.object):
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        resource_item = self.get_resource_item()
        form_link = self.get_delete_link(resource_item)
        response_link = form_link.submit()
        return self.resource.generate_response(self.get_response_media_type(), self.get_response_type(), response_link)

class InlineModelMixin(object):
    def get_changelist_links(self):
        return []
    
    def get_parent(self):
        queryset = self.resource.parent.get_queryset(self.request.user)
        parent = queryset.get(pk=self.kwargs['pk'])
        return parent
    
    def get_queryset(self):
        return self.resource.get_queryset(self.get_parent(), self.request.user)

class InlineModelCreateResourceView(InlineModelMixin, ModelCreateResourceView):
    pass

class InlineModelListResourceView(InlineModelMixin, ModelListResourceView):
    def get_changelist(self):
        if not hasattr(self, '_changelist'):
            self._changelist = self.resource.get_changelist(self.get_parent(), self.request.user, self.request.GET)
        return self._changelist

class InlineModelDetailMixin(object):
    def get_object(self):
        queryset = self.get_queryset()
        return queryset.get(pk=self.kwargs['inline_pk'])

class InlineModelDeleteResourceView(InlineModelDetailMixin, InlineModelMixin, ModelDeleteResourceView):
    pass

class InlineModelDetailResourceView(InlineModelDetailMixin, InlineModelMixin, ModelDetailResourceView):
    pass

