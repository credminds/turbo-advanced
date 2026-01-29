"""
Service functions for settings_config app.

These functions provide a clean interface to retrieve configurations
and interact with third-party services.
"""

import logging

import requests
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def get_stripe_config():
    """
    Retrieve Stripe configuration from database.

    Returns:
        StripeConfiguration instance or None if not active.

    Usage:
        from settings_config.services import get_stripe_config
        config = get_stripe_config()
        if config:
            stripe.api_key = config.secret_key
    """
    from .models import StripeConfiguration

    config = StripeConfiguration.load()
    if config.is_active and config.secret_key:
        return config
    return None


def get_resend_config():
    """
    Retrieve Resend configuration from database.

    Returns:
        ResendConfiguration instance or None if not active.

    Usage:
        from settings_config.services import get_resend_config
        config = get_resend_config()
        if config:
            resend.api_key = config.api_key
    """
    from .models import ResendConfiguration

    config = ResendConfiguration.load()
    if config.is_active and config.api_key:
        return config
    return None


def send_test_email(config, to_email: str) -> tuple[bool, str]:
    """
    Send a test email using Resend API.

    Args:
        config: ResendConfiguration instance
        to_email: Email address to send test to

    Returns:
        Tuple of (success: bool, message: str)
    """
    if not config.api_key:
        return False, _("API key is not configured.")

    if not config.from_email:
        return False, _("From email is not configured.")

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"{config.from_name} <{config.from_email}>"
                if config.from_name
                else config.from_email,
                "to": [to_email],
                "subject": "Test Email - Turbo Configuration",
                "html": """
                    <h1>Test Email Successful!</h1>
                    <p>Your Resend email configuration is working correctly.</p>
                    <p>This email was sent from Turbo Admin settings.</p>
                """,
            },
            timeout=10,
        )

        if response.status_code == 200:
            return True, _("Test email sent successfully to %(email)s") % {
                "email": to_email
            }
        else:
            error_data = response.json()
            error_message = error_data.get("message", response.text)
            logger.error(f"Resend API error: {error_message}")
            return False, _("Failed to send email: %(error)s") % {
                "error": error_message
            }

    except requests.exceptions.Timeout:
        return False, _("Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.exception("Error sending test email")
        return False, _("Failed to send email: %(error)s") % {"error": str(e)}


def send_email(to_email: str, subject: str, html_content: str) -> tuple[bool, str]:
    """
    Send an email using the configured Resend API.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML body content

    Returns:
        Tuple of (success: bool, message: str)

    Usage:
        from settings_config.services import send_email
        success, msg = send_email("user@example.com", "Welcome!", "<h1>Welcome</h1>")
    """
    config = get_resend_config()
    if not config:
        return False, _("Email service is not configured.")

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"{config.from_name} <{config.from_email}>"
                if config.from_name
                else config.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            },
            timeout=10,
        )

        if response.status_code == 200:
            return True, _("Email sent successfully.")
        else:
            error_data = response.json()
            error_message = error_data.get("message", response.text)
            logger.error(f"Resend API error: {error_message}")
            return False, _("Failed to send email: %(error)s") % {
                "error": error_message
            }

    except requests.exceptions.RequestException as e:
        logger.exception("Error sending email")
        return False, _("Failed to send email: %(error)s") % {"error": str(e)}


def get_tinymce_config():
    """
    Retrieve TinyMCE configuration from database.

    Returns:
        TinyMCEConfiguration instance or None if not active.

    Usage:
        from settings_config.services import get_tinymce_config
        config = get_tinymce_config()
        if config:
            mce_config = config.get_config_dict()
            js_url = config.get_js_url()
    """
    from .models import TinyMCEConfiguration

    config = TinyMCEConfiguration.load()
    if config.is_active and config.api_key:
        return config
    return None


def get_cloudinary_config():
    """
    Retrieve Cloudinary configuration from database.

    Returns:
        CloudinaryConfiguration instance or None if not active.

    Usage:
        from settings_config.services import get_cloudinary_config
        config = get_cloudinary_config()
        if config:
            config.configure()  # Configures cloudinary library
    """
    from .models import CloudinaryConfiguration

    config = CloudinaryConfiguration.load()
    if config.is_active and config.cloud_name and config.api_key and config.api_secret:
        return config
    return None


def configure_cloudinary():
    """
    Configure the cloudinary library with database settings.

    Returns:
        bool: True if configured successfully, False otherwise.

    Usage:
        from settings_config.services import configure_cloudinary
        if configure_cloudinary():
            # Cloudinary is ready to use
            import cloudinary.uploader
            result = cloudinary.uploader.upload(file)
    """
    config = get_cloudinary_config()
    if config:
        config.configure()
        return True
    return False


def upload_to_cloudinary(
    image_file,
    folder: str | None = None,
    transformation: dict | None = None,
    timeout: int = 30,
) -> str | None:
    """
    Upload image to Cloudinary using database configuration.

    Args:
        image_file: Django ImageField file or file path
        folder: Cloudinary folder path (uses default from config if not provided)
        transformation: Optional dict with width, height, crop settings
        timeout: Upload timeout in seconds (default: 30)

    Returns:
        str: Cloudinary URL or None if upload fails

    Usage:
        from settings_config.services import upload_to_cloudinary
        url = upload_to_cloudinary(request.FILES['image'], folder='blog/images')
    """
    config = get_cloudinary_config()
    if not config:
        logger.error("Cloudinary is not configured")
        return None

    try:
        import cloudinary
        import cloudinary.uploader

        # Configure cloudinary
        config.configure()

        upload_params = {
            "folder": folder or config.default_folder,
            "resource_type": "image",
            "timeout": timeout,
        }

        if config.auto_optimize:
            upload_params["transformation"] = {
                "quality": "auto:good",
                "fetch_format": "auto",
            }

        if transformation:
            if "transformation" in upload_params:
                upload_params["transformation"].update(transformation)
            else:
                upload_params["transformation"] = transformation

        result = cloudinary.uploader.upload(image_file, **upload_params)
        return result.get("secure_url")

    except Exception as e:
        logger.exception(f"Cloudinary upload error: {e}")
        return None


def delete_from_cloudinary(url: str) -> bool:
    """
    Delete an image from Cloudinary using its URL.

    Args:
        url: The Cloudinary URL of the image to delete

    Returns:
        bool: True if deletion was successful, False otherwise

    Usage:
        from settings_config.services import delete_from_cloudinary
        success = delete_from_cloudinary(old_image_url)
    """
    config = get_cloudinary_config()
    if not config:
        logger.error("Cloudinary is not configured")
        return False

    try:
        import cloudinary
        import cloudinary.uploader

        config.configure()

        # Extract public_id from URL
        parts = url.split("/")
        if "cloudinary.com" in url and len(parts) >= 2:
            upload_index = parts.index("upload")
            public_id_parts = parts[upload_index + 1 :]
            # Remove version if present
            if public_id_parts[0].startswith("v"):
                public_id_parts = public_id_parts[1:]
            public_id = "/".join(public_id_parts)
            # Remove file extension
            public_id = public_id.rsplit(".", 1)[0]

            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        return False

    except Exception as e:
        logger.exception(f"Cloudinary delete error: {e}")
        return False
