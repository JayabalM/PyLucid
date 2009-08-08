# coding: utf-8

"""
    PyLucid.admin
    ~~~~~~~~~~~~~~

    Register all PyLucid model in django admin interface.

    TODO:
        * if http://code.djangoproject.com/ticket/3400 is implement:
            Add site to list_filter for e.g. PageMeta, PageContent etc.      
    
    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate$
    $Rev$
    $Author$

    :copyleft: 2008 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.conf import settings


from reversion.admin import VersionAdmin

from pylucid import models

from pylucid_admin.admin_site import pylucid_admin_site


#------------------------------------------------------------------------------

class BaseAdmin(VersionAdmin):
    def view_on_site_link(self, obj):
        """ view on site link in admin changelist, try to use complete uri with site info. """
        absolute_url = obj.get_absolute_url()
        if hasattr(obj, "get_absolute_uri"):
            url = obj.get_absolute_uri() # complete uri contains protocol and site domain.
        else:
            url = absolute_url

        context = {"absolute_url": absolute_url, "url": url}
        html = render_to_string('admin/pylucid/includes/view_on_site_link.html', context)
        return html

    view_on_site_link.short_description = _("View on site")
    view_on_site_link.allow_tags = True

#------------------------------------------------------------------------------



class PageTreeAdmin(BaseAdmin):
    #prepopulated_fields = {"slug": ("title",)}    

    list_display = ("id", "parent", "slug", "site", "view_on_site_link", "lastupdatetime", "lastupdateby")
    list_display_links = ("id", "slug")
    list_filter = ("site", "page_type", "design", "createby", "lastupdateby",)
    date_hierarchy = 'lastupdatetime'
    search_fields = ("slug",)

pylucid_admin_site.register(models.PageTree, PageTreeAdmin)


class LanguageAdmin(VersionAdmin):
    pass

pylucid_admin_site.register(models.Language, LanguageAdmin)


#class OnSitePageMeta(models.PageMeta):
#    def get_site(self):
#        return self.page.site
#    site = property(get_site)
#    class Meta:
#        proxy = True



class PageMetaAdmin(BaseAdmin):
    list_display = ("id", "get_title", "get_site", "view_on_site_link", "lastupdatetime", "lastupdateby",)
    list_display_links = ("id", "get_title")
    list_filter = ("lang", "createby", "lastupdateby", "tags")#"keywords"
    date_hierarchy = 'lastupdatetime'
    search_fields = ("description", "keywords")


pylucid_admin_site.register(models.PageMeta, PageMetaAdmin)

class PageContentInline(admin.StackedInline):
    model = models.PageContent

class PageContentAdmin(BaseAdmin):
    list_display = ("id", "get_title", "get_site", "view_on_site_link", "lastupdatetime", "lastupdateby",)
    list_display_links = ("id", "get_title")
    list_filter = ("markup", "createby", "lastupdateby",)
    date_hierarchy = 'lastupdatetime'
    search_fields = ("content", "get_title", "absolute_url")

pylucid_admin_site.register(models.PageContent, PageContentAdmin)


class PluginPageAdmin(BaseAdmin):
    list_display = (
        "id", "get_plugin_name", "app_label",
        "get_site", "view_on_site_link", "lastupdatetime", "lastupdateby",
    )
    list_display_links = ("get_plugin_name", "app_label")
    list_filter = ("createby", "lastupdateby",)
    date_hierarchy = 'lastupdatetime'
    search_fields = ("app_label",)

pylucid_admin_site.register(models.PluginPage, PluginPageAdmin)

#-----------------------------------------------------------------------------

#class ColorAdmin(VersionAdmin):
#    list_display = ("id", "name","value")
#pylucid_admin_site.register(models.Color, ColorAdmin)

class ColorInline(admin.TabularInline):
    model = models.Color

class ColorSchemeAdmin(VersionAdmin):
    list_display = ("id", "name", "preview", "lastupdatetime", "lastupdateby")
    list_display_links = ("name",)
    search_fields = ("name",)
    inlines = [ColorInline, ]

    def preview(self, obj):
        colors = models.Color.objects.all().filter(colorscheme=obj)
        result = ""
        for color in colors:
            result += '<span style="background-color:#%s;" title="%s">&nbsp;&nbsp;&nbsp;</span>' % (
                color.value, color.name
            )
        return result
    preview.short_description = 'color preview'
    preview.allow_tags = True

pylucid_admin_site.register(models.ColorScheme, ColorSchemeAdmin)


class DesignAdmin(VersionAdmin):
    list_display = ("id", "name", "template", "colorscheme", "lastupdatetime", "lastupdateby")
    list_display_links = ("name",)
    list_filter = ("site", "template", "colorscheme", "createby", "lastupdateby")
    search_fields = ("name", "template", "colorscheme")

pylucid_admin_site.register(models.Design, DesignAdmin)


class EditableHtmlHeadFileAdmin(VersionAdmin):
    list_display = ("id", "filepath", "site_info", "render", "description", "lastupdatetime", "lastupdateby")
    list_display_links = ("filepath", "description")
    list_filter = ("site", "render")

pylucid_admin_site.register(models.EditableHtmlHeadFile, EditableHtmlHeadFileAdmin)

#-----------------------------------------------------------------------------

class UserProfileAdmin(VersionAdmin):
    list_display = ("id", "user", "site_info", "lastupdatetime", "lastupdateby")
    list_display_links = ("user",)
    list_filter = ("site",)

pylucid_admin_site.register(models.UserProfile, UserProfileAdmin)
