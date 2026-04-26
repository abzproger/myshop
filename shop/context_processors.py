def seo(request):
    """Expose site-wide SEO defaults to templates."""
    from django.conf import settings

    site_url = settings.SITE_URL.rstrip("/")
    default_image = settings.SITE_DEFAULT_IMAGE
    if default_image.startswith("/"):
        default_image = f"{site_url}{default_image}"

    return {
        "site_name": settings.SITE_NAME,
        "site_url": site_url,
        "site_description": settings.SITE_DESCRIPTION,
        "site_default_image": default_image,
        "canonical_url": f"{site_url}{request.path}",
    }
