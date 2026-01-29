import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from settings_config.services import delete_from_cloudinary, upload_to_cloudinary

from .models import User

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def upload_profile_picture_to_cloudinary(sender, instance, **kwargs):
    """
    Upload profile picture to Cloudinary when a new image is uploaded.
    """
    if not instance.pk:
        # New user, check if profile_picture is set
        if instance.profile_picture:
            url = upload_to_cloudinary(
                instance.profile_picture,
                folder="users/profile_pictures",
            )
            if url:
                instance.profile_picture_url = url
                # Clear the file field since we're using URL
                instance.profile_picture = None
        return

    # Existing user - check if profile_picture changed
    try:
        old_instance = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    # If a new profile picture is being uploaded
    if instance.profile_picture and instance.profile_picture != old_instance.profile_picture:
        # Delete old image from Cloudinary if exists
        if old_instance.profile_picture_url:
            delete_from_cloudinary(old_instance.profile_picture_url)

        # Upload new image
        url = upload_to_cloudinary(
            instance.profile_picture,
            folder="users/profile_pictures",
        )
        if url:
            instance.profile_picture_url = url
            # Clear the file field since we're using URL
            instance.profile_picture = None
