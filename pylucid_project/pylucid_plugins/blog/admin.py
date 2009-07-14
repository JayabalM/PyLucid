# coding: utf-8

"""
    PyLucid.admin
    ~~~~~~~~~~~~~~

    Register all PyLucid model in django admin interface.

    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate$
    $Rev$
    $Author$

    :copyleft: 2008 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.auth.admin import UserAdmin

from reversion.admin import VersionAdmin

from blog.models import BlogEntry

class BlogEntryAdmin(VersionAdmin):
    pass
#    #prepopulated_fields = {"slug": ("title",)}    
#
#    list_display = ("id", "parent", "slug", "site", "get_absolute_url", "lastupdatetime", "lastupdateby")
#    list_display_links = ("slug", "get_absolute_url")
#    list_filter = ("site", "page_type", "design", "createby", "lastupdateby",)
#    date_hierarchy = 'lastupdatetime'
#    search_fields = ("slug",)
#
admin.site.register(BlogEntry, BlogEntryAdmin)
