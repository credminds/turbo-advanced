from django import forms
from django.utils.translation import gettext_lazy as _
from unfold.widgets import (
    UnfoldAdminSelectWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminTextInputWidget,
    UnfoldBooleanSwitchWidget,
)

from settings_config.services import get_cloudinary_config, upload_to_cloudinary

from .models import Newsletter, NewsletterSubscriber, Post


class PostAdminForm(forms.ModelForm):
    """Custom form for Post admin with TinyMCE and Cloudinary integration."""

    featured_image_file = forms.ImageField(
        required=False,
        label=_("Upload Featured Image"),
        help_text=_("Upload a new image (will be stored in Cloudinary)"),
    )

    class Meta:
        model = Post
        fields = "__all__"
        widgets = {
            "title": UnfoldAdminTextInputWidget(),
            "slug": UnfoldAdminTextInputWidget(),
            "excerpt": UnfoldAdminTextareaWidget(attrs={"rows": 3}),
            "featured_image_url": UnfoldAdminTextInputWidget(
                attrs={"placeholder": "https://res.cloudinary.com/..."}
            ),
            "status": UnfoldAdminSelectWidget(),
            "is_featured": UnfoldBooleanSwitchWidget(),
            "meta_title": UnfoldAdminTextInputWidget(),
            "meta_description": UnfoldAdminTextareaWidget(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if Cloudinary is configured
        if not get_cloudinary_config():
            self.fields["featured_image_file"].help_text = _(
                "Cloudinary is not configured. Please configure it in System Settings."
            )
            self.fields["featured_image_file"].disabled = True

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle Cloudinary upload
        if self.cleaned_data.get("featured_image_file"):
            url = upload_to_cloudinary(
                self.cleaned_data["featured_image_file"],
                folder="blog/featured",
            )
            if url:
                instance.featured_image_url = url

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class NewsletterAdminForm(forms.ModelForm):
    """Custom form for Newsletter admin with TinyMCE."""

    class Meta:
        model = Newsletter
        fields = "__all__"
        widgets = {
            "subject": UnfoldAdminTextInputWidget(),
            "status": UnfoldAdminSelectWidget(),
        }


class NewsletterSubscriberAdminForm(forms.ModelForm):
    """Custom form for Newsletter Subscriber admin."""

    class Meta:
        model = NewsletterSubscriber
        fields = "__all__"
        widgets = {
            "email": UnfoldAdminTextInputWidget(),
            "name": UnfoldAdminTextInputWidget(),
            "status": UnfoldAdminSelectWidget(),
        }
