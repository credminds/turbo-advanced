from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = [
        "display_avatar",
        "username",
        "email",
        "first_name",
        "last_name",
        "display_staff_status",
        "display_active_status",
    ]
    list_display_links = ["display_avatar", "username"]
    search_fields = ["username", "email", "first_name", "last_name"]
    list_filter = ["is_staff", "is_superuser", "is_active", "groups"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "profile_picture",
                    "profile_picture_url",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    @display(description=_("User"))
    def display_avatar(self, instance):
        name = instance.get_full_name() or instance.username
        if instance.profile_picture_url and instance.profile_picture_url.startswith(
            "http"
        ):
            return format_html(
                '<div style="display: flex; align-items: center; gap: 10px;">'
                '<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />'
                '<div><strong>{}</strong><br><span style="color: #666; font-size: 12px;">{}</span></div>'
                "</div>",
                instance.profile_picture_url,
                name,
                instance.email or "-",
            )
        return format_html(
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<div style="width: 40px; height: 40px; border-radius: 50%; background: #e5e7eb; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-weight: bold;">{}</div>'
            '<div><strong>{}</strong><br><span style="color: #666; font-size: 12px;">{}</span></div>'
            "</div>",
            name[0].upper() if name else "?",
            name,
            instance.email or "-",
        )

    @display(
        description=_("Staff"),
        label={
            True: "success",
            False: "info",
        },
    )
    def display_staff_status(self, instance):
        return instance.is_staff

    @display(
        description=_("Active"),
        label={
            True: "success",
            False: "danger",
        },
    )
    def display_active_status(self, instance):
        return instance.is_active


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
