from django import forms
from django.contrib import admin, messages
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.widgets import (
    UnfoldAdminEmailInputWidget,
    UnfoldAdminIntegerFieldWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminTextInputWidget,
    UnfoldBooleanSwitchWidget,
)

from .models import (
    CloudinaryConfiguration,
    ResendConfiguration,
    StripeConfiguration,
    TinyMCEConfiguration,
)
from .services import send_test_email


class SingletonModelAdmin(ModelAdmin):
    """Admin for singleton models - redirects to the single instance."""

    formfield_overrides = {
        models.CharField: {"widget": UnfoldAdminTextInputWidget},
        models.TextField: {"widget": UnfoldAdminTextareaWidget},
        models.EmailField: {"widget": UnfoldAdminEmailInputWidget},
        models.BooleanField: {"widget": UnfoldBooleanSwitchWidget},
        models.PositiveIntegerField: {"widget": UnfoldAdminIntegerFieldWidget},
    }

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = self.model.objects.get_or_create(pk=1)
        return HttpResponseRedirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )


class StripeConfigurationForm(forms.ModelForm):
    class Meta:
        model = StripeConfiguration
        fields = "__all__"
        widgets = {
            "is_active": UnfoldBooleanSwitchWidget(),
            "is_live_mode": UnfoldBooleanSwitchWidget(),
            "publishable_key": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "pk_test_... or pk_live_..."}
            ),
            "secret_key": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "sk_test_... or sk_live_..."}
            ),
            "webhook_secret": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "whsec_..."}
            ),
        }


@admin.register(StripeConfiguration)
class StripeConfigurationAdmin(SingletonModelAdmin):
    form = StripeConfigurationForm
    list_display = ["__str__", "display_status", "display_mode", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Status"),
            {
                "fields": ("is_active", "is_live_mode"),
                "classes": ["tab"],
            },
        ),
        (
            _("API Keys"),
            {
                "fields": ("publishable_key", "secret_key", "webhook_secret"),
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
            True: "success",
            False: "danger",
        },
    )
    def display_status(self, instance):
        return instance.is_active

    @display(
        description=_("Mode"),
        label={
            True: "warning",
            False: "info",
        },
    )
    def display_mode(self, instance):
        return instance.is_live_mode


class ResendConfigurationForm(forms.ModelForm):
    class Meta:
        model = ResendConfiguration
        fields = "__all__"
        widgets = {
            "is_active": UnfoldBooleanSwitchWidget(),
            "api_key": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "re_..."}
            ),
            "from_email": UnfoldAdminEmailInputWidget(
                attrs={"placeholder": "noreply@yourdomain.com"}
            ),
            "from_name": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "Your App Name"}
            ),
        }


@admin.register(ResendConfiguration)
class ResendConfigurationAdmin(SingletonModelAdmin):
    form = ResendConfigurationForm
    list_display = [
        "__str__",
        "display_status",
        "display_test_status",
        "last_test_at",
        "updated_at",
    ]
    readonly_fields = ["created_at", "updated_at", "last_test_at", "last_test_status"]

    fieldsets = (
        (
            _("Status"),
            {
                "fields": ("is_active",),
                "classes": ["tab"],
            },
        ),
        (
            _("API Configuration"),
            {
                "fields": ("api_key",),
                "classes": ["tab"],
            },
        ),
        (
            _("Sender Settings"),
            {
                "fields": ("from_email", "from_name"),
                "classes": ["tab"],
            },
        ),
        (
            _("Test Email"),
            {
                "fields": ("last_test_status", "last_test_at"),
                "classes": ["tab"],
                "description": _(
                    "Use the 'Send Test Email' button above to verify your configuration."
                ),
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
            True: "success",
            False: "danger",
        },
    )
    def display_status(self, instance):
        return instance.is_active

    @display(
        description=_("Test Status"),
        label={
            "success": "success",
            "failed": "danger",
            "": "warning",
        },
    )
    def display_test_status(self, instance):
        return instance.last_test_status or ""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/send-test-email/",
                self.admin_site.admin_view(self.send_test_email_view),
                name="settings_config_resendconfiguration_send_test_email",
            ),
        ]
        return custom_urls + urls

    def send_test_email_view(self, request, pk):
        config = self.get_object(request, pk)
        test_email = request.POST.get("test_email", "")

        if not test_email:
            messages.error(request, _("Please provide a test email address."))
            return HttpResponseRedirect(
                reverse(
                    "admin:settings_config_resendconfiguration_change",
                    args=[pk],
                )
            )

        success, message = send_test_email(config, test_email)

        if success:
            config.last_test_status = "success"
            config.last_test_at = timezone.now()
            config.save()
            messages.success(request, message)
        else:
            config.last_test_status = "failed"
            config.save()
            messages.error(request, message)

        return HttpResponseRedirect(
            reverse(
                "admin:settings_config_resendconfiguration_change",
                args=[pk],
            )
        )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_test_email_form"] = True
        extra_context["test_email_url"] = reverse(
            "admin:settings_config_resendconfiguration_send_test_email",
            args=[object_id],
        )
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )


class TinyMCEConfigurationForm(forms.ModelForm):
    class Meta:
        model = TinyMCEConfiguration
        fields = "__all__"
        widgets = {
            "is_active": UnfoldBooleanSwitchWidget(),
            "api_key": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "Your TinyMCE Cloud API key"}
            ),
            "height": UnfoldAdminIntegerFieldWidget(
                attrs={"placeholder": "500"}
            ),
            "menubar": UnfoldAdminTextInputWidget(),
            "plugins": UnfoldAdminTextareaWidget(
                attrs={"rows": 3, "placeholder": "advlist autolink lists link image..."}
            ),
            "toolbar": UnfoldAdminTextareaWidget(
                attrs={"rows": 3, "placeholder": "undo redo | blocks | bold italic..."}
            ),
        }


@admin.register(TinyMCEConfiguration)
class TinyMCEConfigurationAdmin(SingletonModelAdmin):
    form = TinyMCEConfigurationForm
    list_display = ["__str__", "display_status", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Status"),
            {
                "fields": ("is_active",),
                "classes": ["tab"],
            },
        ),
        (
            _("API Configuration"),
            {
                "fields": ("api_key",),
                "classes": ["tab"],
            },
        ),
        (
            _("Editor Settings"),
            {
                "fields": ("height", "menubar", "plugins", "toolbar"),
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
            True: "success",
            False: "danger",
        },
    )
    def display_status(self, instance):
        return instance.is_active


class CloudinaryConfigurationForm(forms.ModelForm):
    class Meta:
        model = CloudinaryConfiguration
        fields = "__all__"
        widgets = {
            "is_active": UnfoldBooleanSwitchWidget(),
            "auto_optimize": UnfoldBooleanSwitchWidget(),
            "cloud_name": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "your-cloud-name"}
            ),
            "api_key": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "123456789012345"}
            ),
            "api_secret": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "your-api-secret"}
            ),
            "default_folder": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "uploads"}
            ),
        }


@admin.register(CloudinaryConfiguration)
class CloudinaryConfigurationAdmin(SingletonModelAdmin):
    form = CloudinaryConfigurationForm
    list_display = ["__str__", "display_status", "cloud_name", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Status"),
            {
                "fields": ("is_active",),
                "classes": ["tab"],
            },
        ),
        (
            _("API Configuration"),
            {
                "fields": ("cloud_name", "api_key", "api_secret"),
                "classes": ["tab"],
            },
        ),
        (
            _("Upload Settings"),
            {
                "fields": ("default_folder", "auto_optimize"),
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
            True: "success",
            False: "danger",
        },
    )
    def display_status(self, instance):
        return instance.is_active
