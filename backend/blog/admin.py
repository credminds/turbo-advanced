from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.widgets import (
    UnfoldAdminSelectWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminTextInputWidget,
    UnfoldBooleanSwitchWidget,
)

from settings_config.services import get_tinymce_config

from .forms import NewsletterAdminForm, NewsletterSubscriberAdminForm, PostAdminForm
from .models import Category, Newsletter, NewsletterSubscriber, Post, Tag


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name", "slug", "post_count", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}

    formfield_overrides = {
        models.CharField: {"widget": UnfoldAdminTextInputWidget},
        models.TextField: {"widget": UnfoldAdminTextareaWidget},
    }

    def post_count(self, obj):
        return obj.posts.count()

    post_count.short_description = _("Posts")


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ["name", "slug", "post_count"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}

    formfield_overrides = {
        models.CharField: {"widget": UnfoldAdminTextInputWidget},
    }

    def post_count(self, obj):
        return obj.posts.count()

    post_count.short_description = _("Posts")


@admin.register(Post)
class PostAdmin(ModelAdmin):
    form = PostAdminForm
    list_display = [
        "title",
        "display_status",
        "display_featured",
        "author",
        "category",
        "published_at",
    ]
    list_filter = [
        "status",
        "is_featured",
        "category",
    ]
    search_fields = ["title", "excerpt", "content"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["author", "category", "tags"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "published_at"

    fieldsets = (
        (
            _("Content"),
            {
                "fields": ("title", "slug", "excerpt", "content"),
                "classes": ["tab"],
            },
        ),
        (
            _("Featured Image"),
            {
                "fields": ("featured_image_file", "featured_image_url"),
                "classes": ["tab"],
            },
        ),
        (
            _("Classification"),
            {
                "fields": ("author", "category", "tags"),
                "classes": ["tab"],
            },
        ),
        (
            _("Publishing"),
            {
                "fields": ("status", "is_featured", "published_at"),
                "classes": ["tab"],
            },
        ),
        (
            _("SEO"),
            {
                "fields": ("meta_title", "meta_description"),
                "classes": ["tab"],
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ["tab"],
            },
        ),
    )

    @display(
        description=_("Status"),
        label={
            Post.Status.DRAFT: "warning",
            Post.Status.PUBLISHED: "success",
            Post.Status.ARCHIVED: "info",
        },
    )
    def display_status(self, instance):
        return instance.status

    @display(
        description=_("Featured"),
        label={
            True: "success",
            False: "info",
        },
    )
    def display_featured(self, instance):
        return instance.is_featured

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        tinymce_config = get_tinymce_config()
        if tinymce_config:
            extra_context["tinymce_config"] = tinymce_config.get_config_dict()
            extra_context["tinymce_js_url"] = tinymce_config.get_js_url()
        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        tinymce_config = get_tinymce_config()
        if tinymce_config:
            extra_context["tinymce_config"] = tinymce_config.get_config_dict()
            extra_context["tinymce_js_url"] = tinymce_config.get_js_url()
        return super().add_view(request, form_url, extra_context)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(ModelAdmin):
    form = NewsletterSubscriberAdminForm
    list_display = ["email", "name", "display_status", "created_at"]
    list_filter = ["status"]
    search_fields = ["email", "name"]
    readonly_fields = ["confirmation_token", "confirmed_at", "unsubscribed_at", "created_at"]

    formfield_overrides = {
        models.CharField: {"widget": UnfoldAdminTextInputWidget},
        models.EmailField: {"widget": UnfoldAdminTextInputWidget},
    }

    fieldsets = (
        (
            _("Subscriber Info"),
            {
                "fields": ("email", "name", "status"),
                "classes": ["tab"],
            },
        ),
        (
            _("Status Details"),
            {
                "fields": ("confirmation_token", "confirmed_at", "unsubscribed_at", "created_at"),
                "classes": ["tab"],
            },
        ),
    )

    @display(
        description=_("Status"),
        label={
            NewsletterSubscriber.Status.PENDING: "warning",
            NewsletterSubscriber.Status.ACTIVE: "success",
            NewsletterSubscriber.Status.UNSUBSCRIBED: "danger",
        },
    )
    def display_status(self, instance):
        return instance.status


@admin.register(Newsletter)
class NewsletterAdmin(ModelAdmin):
    form = NewsletterAdminForm
    list_display = ["subject", "display_status", "recipients_count", "scheduled_at", "sent_at"]
    list_filter = ["status"]
    search_fields = ["subject", "content"]
    readonly_fields = ["sent_at", "recipients_count", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Content"),
            {
                "fields": ("subject", "content"),
                "classes": ["tab"],
            },
        ),
        (
            _("Scheduling"),
            {
                "fields": ("status", "scheduled_at"),
                "classes": ["tab"],
            },
        ),
        (
            _("Delivery Info"),
            {
                "fields": ("sent_at", "recipients_count"),
                "classes": ["tab"],
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ["tab"],
            },
        ),
    )

    @display(
        description=_("Status"),
        label={
            Newsletter.Status.DRAFT: "warning",
            Newsletter.Status.SCHEDULED: "info",
            Newsletter.Status.SENT: "success",
        },
    )
    def display_status(self, instance):
        return instance.status
