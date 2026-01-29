from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """Blog post categories."""

    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True, blank=True)
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Blog post tags."""

    name = models.CharField(_("Name"), max_length=50)
    slug = models.SlugField(_("Slug"), max_length=50, unique=True, blank=True)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    """Blog posts."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")
        ARCHIVED = "archived", _("Archived")

    title = models.CharField(_("Title"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, unique=True, blank=True)
    excerpt = models.TextField(
        _("Excerpt"),
        blank=True,
        help_text=_("Brief summary of the post (shown in listings)"),
    )
    content = models.TextField(_("Content"), blank=True)
    featured_image_url = models.URLField(
        _("Featured Image URL"),
        blank=True,
        help_text=_("URL to the featured image (Cloudinary)"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="blog_posts",
        verbose_name=_("Author"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name=_("Category"),
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="posts",
        verbose_name=_("Tags"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    is_featured = models.BooleanField(
        _("Featured"),
        default=False,
        help_text=_("Show in featured posts section"),
    )
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    # SEO fields
    meta_title = models.CharField(
        _("Meta Title"),
        max_length=70,
        blank=True,
        help_text=_("SEO title (max 70 chars)"),
    )
    meta_description = models.CharField(
        _("Meta Description"),
        max_length=160,
        blank=True,
        help_text=_("SEO description (max 160 chars)"),
    )

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Auto-set published_at when status changes to published
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class NewsletterSubscriber(models.Model):
    """Newsletter subscribers."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending Confirmation")
        ACTIVE = "active", _("Active")
        UNSUBSCRIBED = "unsubscribed", _("Unsubscribed")

    email = models.EmailField(_("Email"), unique=True)
    name = models.CharField(_("Name"), max_length=100, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    confirmation_token = models.CharField(
        _("Confirmation Token"),
        max_length=100,
        blank=True,
    )
    confirmed_at = models.DateTimeField(_("Confirmed at"), null=True, blank=True)
    unsubscribed_at = models.DateTimeField(_("Unsubscribed at"), null=True, blank=True)
    created_at = models.DateTimeField(_("Subscribed at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Newsletter Subscriber")
        verbose_name_plural = _("Newsletter Subscribers")
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class Newsletter(models.Model):
    """Newsletter campaigns."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SCHEDULED = "scheduled", _("Scheduled")
        SENT = "sent", _("Sent")

    subject = models.CharField(_("Subject"), max_length=255)
    content = models.TextField(_("Content"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    scheduled_at = models.DateTimeField(_("Scheduled at"), null=True, blank=True)
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    recipients_count = models.PositiveIntegerField(_("Recipients"), default=0)
    created_at = models.DateTimeField(_("Created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Newsletter")
        verbose_name_plural = _("Newsletters")
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject
