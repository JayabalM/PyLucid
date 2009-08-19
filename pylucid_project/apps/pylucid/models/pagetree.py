# coding: utf-8

"""
    PyLucid models
    ~~~~~~~~~~~~~~

    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate: $
    $Rev: $
    $Author: $

    :copyleft: 2009 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from xml.sax.saxutils import escape

from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.auth.models import Group

# http://code.google.com/p/django-tools/
from django_tools.middlewares import ThreadLocal
from django_tools import model_utils

from pylucid.tree_model import BaseTreeModel, TreeGenerator
from pylucid.models.base_models import BaseModel, BaseModelManager, UpdateInfoBaseModel

from pylucid_plugins import update_journal

# Other PyLucid models
from design import Design
from pagemeta import PageMeta
from pagecontent import PageContent


TAG_INPUT_HELP_URL = \
"http://google.com/search?q=cache:django-tagging.googlecode.com/files/tagging-0.2-overview.html#tag-input"



class PageTreeManager(BaseModelManager):
    """
    Manager class for PageTree model

    inherited from models.Manager:
        get_or_create() method, witch expected a request object as the first argument.
    """
    def filter_accessible(self, queryset, user):
        """ filter all pages with can't accessible for the given user """

        if user.is_anonymous():
            # Anonymous user are in no user group
            return queryset.filter(permitViewGroup__isnull=True)

        if user.is_superuser:
            # Superuser can see everything ;)
            return queryset

        # filter pages for not superuser and not anonymous

        user_groups = user.groups.values_list('pk', flat=True)

        if not user_groups:
            # User is in no group
            return queryset.filter(permitViewGroup__isnull=True)

        # Filter out all view group
        return queryset.filter(
            models.Q(permitViewGroup__isnull=True) | models.Q(permitViewGroup__in=user_groups)
        )

    def all_accessible(self, user=None):
        """ returns all pages that the given user can access. """
        if user == None:
            user = ThreadLocal.get_current_user()

        queryset = self.model.on_site
        queryset = self.filter_accessible(queryset, user)
        return queryset

    def get_tree(self, user=None, filter_showlinks=False):
        """ return a TreeGenerator instance with all accessable page tree instance """
        queryset = self.all_accessible(user)

        if filter_showlinks:
            # Filter PageTree.showlinks
            queryset = queryset.filter(showlinks=True)

        queryset = queryset.order_by("position")
        items = queryset.values("id", "parent")
        tree = TreeGenerator(items, skip_no_parent=True)
        return tree

    def get_choices(self, user=None):
        """ returns a choices list for e.g. a forms select widget. """
        tree = PageTree.objects.get_tree(user)
        choices = [("", "---------")] + [
            (node.db_instance.pk, node.db_instance.get_absolute_url())
            for node in tree.iter_flat_list()
        ]
        return choices


#    def easy_create(self, cleaned_form_data, page_type):
#        """
#        Creating a new PageTree entry with cleaned form data witch can hold more data than for
#        this model
#        """
#        pagetree_kwargs = form_utils.make_kwargs(
#            cleaned_form_data, keys=PageTree._meta.get_all_field_names()
#        )
#        assert page_type in PageTree.TYPE_DICT
#        pagetree_kwargs["type"] = page_type
#
#        pagetree_instance = PageTree(**pagetree_kwargs)
#        pagetree_instance.save()
#        return pagetree_instance

    def get_root_page(self, user, filter_parent=True):
        """ returns the 'first' root page tree entry witch the user can access """
        queryset = self.all_accessible(user)

        if filter_parent:
            # All "root" pages
            queryset = queryset.filter(parent=None).order_by("position")
        else:
            # fallback if no "root" page is accessable
            queryset = queryset.order_by("parent", "position")

        try:
            return queryset[0]
        except IndexError, err:
            if self.model.on_site.count() == 0:
                raise PageTree.DoesNotExist("There exist no PageTree items! Have you install PyLucid?")
            elif filter_parent == True:
                # If all root pages not accessible for the current user
                # -> try to get the first accessable page
                return self.get_root_page(user, filter_parent=False)
            else:
                raise

    def get_model_instance(self, request, ModelClass, pagetree=None, show_lang_info=True):
        """
        Shared function for getting a model instance from the given model witch has
        a foreignkey to PageTree and Language model.
        Use the current language or the system default language.
        If pagetree==None: Use request.PYLUCID.pagetree
        If show_lang_info: Create a page_msg if requested item doesn't exist in client favored language.
        """
        # client favored Language instance:
        lang_entry = request.PYLUCID.lang_entry
        # default Language instance set in system preferences:
        default_lang_entry = request.PYLUCID.default_lang_entry

        lang_entry = request.PYLUCID.lang_entry
        default_lang_entry = request.PYLUCID.default_lang_entry

        if not pagetree:
            # current pagetree instance
            pagetree = request.PYLUCID.pagetree

        queryset = ModelClass.objects.all().filter(page=pagetree)
        try:
            # Try to get the current used language
            return queryset.get(lang=lang_entry)
        except ModelClass.DoesNotExist:
            # Get the PageContent entry in the system default language
            try:
                instance = queryset.get(lang=default_lang_entry)
            except ModelClass.DoesNotExist, err:
                msg = (
                    "%r doesn't exist for %r in client favored language %r"
                    " and not in system default language %r!"
                    " Original Error was: %s"
                ) % (ModelClass, pagetree, lang_entry, default_lang_entry, err)
                raise ModelClass.DoesNotExist(msg)

            if show_lang_info and (settings.DEBUG or settings.PYLUCID.I18N_DEBUG):
                request.page_msg.error(
                    "Page '%s' doesn't exist in client favored language '%s', use '%s' entry." % (
                        pagetree.slug, lang_entry.code, instance.lang.code
                    )
                )
            return instance


    def get_pagemeta(self, request, pagetree=None, show_lang_info=False):
        """
        Returns the PageMeta instance for pagetree and language.
        If there is no PageMeta in the current language, use the system default language.
        If pagetree==None: Use request.PYLUCID.pagetree
        """
        return self.get_model_instance(request, PageMeta, pagetree, show_lang_info)

    def get_pagecontent(self, request, pagetree=None, show_lang_info=False):
        """
        Returns the PageContent instance for pagetree and language.
        If there is no PageContent in the current language, use the system default language.
        If pagetree==None: Use request.PYLUCID.pagetree
        """
        pagemeta = self.get_model_instance(request, PageMeta, pagetree, show_lang_info)
        pagecontent = PageContent.objects.get(pagemeta=pagemeta)
        return pagecontent

    def get_page_from_url(self, request, url_path):
        """
        returns a tuple the page tree instance from the given url_path
        XXX: move it out from model?
        """
        if not request.user.is_superuser:
            user_groups = request.user.groups.all()

        path = url_path.split("/")
        page = None
        for no, page_slug in enumerate(path):
            try:
                page = PageTree.on_site.get(parent=page, slug=page_slug)
            except PageTree.DoesNotExist:
                raise PageTree.DoesNotExist("Wrong url part: %s" % escape(page_slug))

            page_view_group = page.permitViewGroup

            # Check permissions
            if request.user.is_anonymous():
                # Anonymous user are in no user group
                if page_view_group != None:
                    # XXX: raise permission deny?
                    msg = "Permission deny"
                    if settings.DEBUG:
                        msg += " (url part: %s)" % escape(page_slug)
                    raise PageTree.DoesNotExist(msg)
            elif not request.user.is_superuser: # Superuser can see everything ;)
                if (page_view_group != None) and (page_view_group not in user_groups):
                    msg = "Permission deny"
                    if settings.DEBUG:
                        msg += " (not in view group %r, url part: %r)" % (page_view_group, escape(page_slug))
                    raise PageTree.DoesNotExist(msg)

            if page.page_type == PageTree.PLUGIN_TYPE:
                # It's a plugin
                prefix_url = "/".join(path[:no + 1])
                rest_url = "/".join(path[no + 1:])
#                if not rest_url.endswith("/"):
#                    rest_url += "/"
                return (page, prefix_url, rest_url)

        return (page, None, None)

    def get_backlist(self, request, pagetree=None):
        """
        Generate a list of backlinks, usefull for generating a "You are here" breadcrumb navigation.
        TODO: filter showlinks and permit settings
        TODO: filter current site
        FIXME: Think this created many database requests
        """
        if pagetree == None:
            pagetree = request.PYLUCID.pagetree

        pagemeta = self.get_pagemeta(request, pagetree)
        url = pagemeta.get_absolute_url()
        page_name = pagemeta.get_name()
        page_title = pagemeta.get_title()

        backlist = [{"url": url, "name": page_name, "title": page_title}]

        parent = pagetree.parent
        if parent:
            # insert parent links
            backlist = self.get_backlist(request, parent) + backlist

        return backlist


class PageTree(BaseModel, BaseTreeModel, UpdateInfoBaseModel):
    """
    The CMS page tree

    inherited attributes from TreeBaseModel:
        parent
        position

    inherited attributes from UpdateInfoBaseModel:
        createtime     -> datetime of creation
        lastupdatetime -> datetime of the last change
        createby       -> ForeignKey to user who creaded this entry
        lastupdateby   -> ForeignKey to user who has edited this entry
    """
    PAGE_TYPE = 'C'
    PLUGIN_TYPE = 'P'

    TYPE_CHOICES = (
        (PAGE_TYPE, 'CMS-Page'),
        (PLUGIN_TYPE , 'PluginPage'),
    )
    TYPE_DICT = dict(TYPE_CHOICES)

    objects = PageTreeManager()

    slug = models.SlugField(unique=False, help_text="(for building URLs)")

    site = models.ForeignKey(Site, default=Site.objects.get_current)
    on_site = CurrentSiteManager()

    page_type = models.CharField(max_length=1, choices=TYPE_CHOICES)

    design = models.ForeignKey(Design, help_text="Page Template, CSS/JS files")

    showlinks = models.BooleanField(default=True,
        help_text="Accessable for all users, but don't put a Link to this page into menu/sitemap etc."
    )
    permitViewGroup = models.ForeignKey(Group, related_name="%(class)s_permitViewGroup",
        help_text="Limit viewable to a group?",
        null=True, blank=True,
    )
    permitEditGroup = models.ForeignKey(Group, related_name="%(class)s_permitEditGroup",
        help_text="Usergroup how can edit this page.",
        null=True, blank=True,
    )

    _url_cache = {}
    def get_absolute_url(self):
        """ absolute url *without* language code (without domain/host part) """
        if self.pk in self._url_cache:
            #print "PageTree url cache len: %s, pk: %s" % (len(self._url_cache), self.pk)
            return self._url_cache[self.pk]

        if self.parent:
            parent_shortcut = self.parent.get_absolute_url()
            url = parent_shortcut + self.slug + "/"
        else:
            url = "/" + self.slug + "/"

        self._url_cache[self.pk] = url
        return url

    def save(self, *args, **kwargs):
        """ reset PageMeta and PageTree url cache """
        self._url_cache.clear()
        PageMeta._url_cache.clear()
        return super(PageTree, self).save(*args, **kwargs)

    def get_site(self):
        """ used e.g. for self.get_absolute_uri() and the admin page """
        return self.site

    def __unicode__(self):
        return u"PageTree %r (id: %i, site: %s, type: %s)" % (
            self.slug, self.id, self.site.domain, self.TYPE_DICT.get(self.page_type)
        )

    class Meta:
        app_label = 'pylucid'
        verbose_name_plural = verbose_name = "PageTree"
        unique_together = (("site", "slug", "parent"),)

        # FIXME: It would be great if we can order by get_absolute_url()
#        ordering = ("site", "id", "position")
        ordering = ("-lastupdatetime",)

# Check Meta.unique_together manually
model_utils.auto_add_check_unique_together(PageTree)