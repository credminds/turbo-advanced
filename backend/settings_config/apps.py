from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SettingsConfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "settings_config"
    verbose_name = _("System Settings")
