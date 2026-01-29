from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _


class SingletonModel(models.Model):
    """Base model that ensures only one instance exists."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        self.clear_cache()

    def delete(self, *args, **kwargs):
        self.clear_cache()
        super().delete(*args, **kwargs)

    @classmethod
    def load(cls):
        """Load the singleton instance, creating it if it doesn't exist."""
        cache_key = f"{cls.__name__}_singleton"
        instance = cache.get(cache_key)
        if instance is None:
            instance, _ = cls.objects.get_or_create(pk=1)
            cache.set(cache_key, instance, timeout=300)  # Cache for 5 minutes
        return instance

    def clear_cache(self):
        cache_key = f"{self.__class__.__name__}_singleton"
        cache.delete(cache_key)


class StripeConfiguration(SingletonModel):
    """Stripe API configuration settings."""

    is_active = models.BooleanField(
        _("Active"),
        default=False,
        help_text=_("Enable Stripe integration"),
    )
    publishable_key = models.CharField(
        _("Publishable Key"),
        max_length=255,
        blank=True,
        help_text=_("Stripe publishable key (pk_test_... or pk_live_...)"),
    )
    secret_key = models.CharField(
        _("Secret Key"),
        max_length=255,
        blank=True,
        help_text=_("Stripe secret key (sk_test_... or sk_live_...)"),
    )
    webhook_secret = models.CharField(
        _("Webhook Secret"),
        max_length=255,
        blank=True,
        help_text=_("Stripe webhook signing secret (whsec_...)"),
    )
    is_live_mode = models.BooleanField(
        _("Live Mode"),
        default=False,
        help_text=_("Use live mode keys (uncheck for test mode)"),
    )
    created_at = models.DateTimeField(_("Created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Stripe Configuration")
        verbose_name_plural = _("Stripe Configuration")

    def __str__(self):
        mode = "Live" if self.is_live_mode else "Test"
        status = "Active" if self.is_active else "Inactive"
        return f"Stripe Configuration ({mode} - {status})"


class ResendConfiguration(SingletonModel):
    """Resend email API configuration settings."""

    is_active = models.BooleanField(
        _("Active"),
        default=False,
        help_text=_("Enable Resend email integration"),
    )
    api_key = models.CharField(
        _("API Key"),
        max_length=255,
        blank=True,
        help_text=_("Resend API key (re_...)"),
    )
    from_email = models.EmailField(
        _("From Email"),
        max_length=255,
        blank=True,
        help_text=_("Default sender email address"),
    )
    from_name = models.CharField(
        _("From Name"),
        max_length=255,
        blank=True,
        help_text=_("Default sender name"),
    )
    last_test_at = models.DateTimeField(
        _("Last Test"),
        null=True,
        blank=True,
        help_text=_("Last successful test email sent"),
    )
    last_test_status = models.CharField(
        _("Test Status"),
        max_length=50,
        blank=True,
        choices=[
            ("", "Not Tested"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="",
    )
    created_at = models.DateTimeField(_("Created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Resend Configuration")
        verbose_name_plural = _("Resend Configuration")

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"Resend Configuration ({status})"


class TinyMCEConfiguration(SingletonModel):
    """TinyMCE rich text editor configuration settings."""

    is_active = models.BooleanField(
        _("Active"),
        default=False,
        help_text=_("Enable TinyMCE editor"),
    )
    api_key = models.CharField(
        _("API Key"),
        max_length=255,
        blank=True,
        help_text=_("TinyMCE Cloud API key (get from tiny.cloud)"),
    )
    height = models.PositiveIntegerField(
        _("Editor Height"),
        default=500,
        help_text=_("Editor height in pixels"),
    )
    menubar = models.CharField(
        _("Menu Bar"),
        max_length=255,
        default="file edit view insert format tools table help",
        help_text=_("Menu bar items"),
    )
    plugins = models.TextField(
        _("Plugins"),
        default="advlist autolink lists link image charmap preview anchor searchreplace visualblocks code fullscreen insertdatetime media table help wordcount",
        help_text=_("Space-separated list of plugins"),
    )
    toolbar = models.TextField(
        _("Toolbar"),
        default="undo redo | blocks | bold italic forecolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | image media link | code | help",
        help_text=_("Toolbar configuration"),
    )
    created_at = models.DateTimeField(_("Created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("TinyMCE Configuration")
        verbose_name_plural = _("TinyMCE Configuration")

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"TinyMCE Configuration ({status})"

    def get_config_dict(self):
        """Return TinyMCE configuration as a dictionary."""
        return {
            "height": self.height,
            "menubar": self.menubar,
            "plugins": self.plugins.split(),
            "toolbar": self.toolbar,
            "content_css": "default",
            "relative_urls": False,
            "remove_script_host": False,
            "convert_urls": True,
            "branding": False,
            "promotion": False,
            "referrer_policy": "origin",
        }

    def get_js_url(self):
        """Return the TinyMCE CDN URL with API key."""
        if self.api_key:
            return f"https://cdn.tiny.cloud/1/{self.api_key}/tinymce/7/tinymce.min.js"
        return None


class CloudinaryConfiguration(SingletonModel):
    """Cloudinary media storage configuration settings."""

    is_active = models.BooleanField(
        _("Active"),
        default=False,
        help_text=_("Enable Cloudinary integration"),
    )
    cloud_name = models.CharField(
        _("Cloud Name"),
        max_length=255,
        blank=True,
        help_text=_("Cloudinary cloud name"),
    )
    api_key = models.CharField(
        _("API Key"),
        max_length=255,
        blank=True,
        help_text=_("Cloudinary API key"),
    )
    api_secret = models.CharField(
        _("API Secret"),
        max_length=255,
        blank=True,
        help_text=_("Cloudinary API secret"),
    )
    default_folder = models.CharField(
        _("Default Folder"),
        max_length=255,
        default="uploads",
        help_text=_("Default folder for uploads in Cloudinary"),
    )
    auto_optimize = models.BooleanField(
        _("Auto Optimize"),
        default=True,
        help_text=_("Automatically optimize images (quality and format)"),
    )
    created_at = models.DateTimeField(_("Created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Cloudinary Configuration")
        verbose_name_plural = _("Cloudinary Configuration")

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"Cloudinary Configuration ({status})"

    def configure(self):
        """Configure the cloudinary library with these settings."""
        import cloudinary

        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )
