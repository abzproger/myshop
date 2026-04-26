from django.conf import settings
from django.http import HttpResponse


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /cart/",
        "Disallow: /orders/",
        "Disallow: /users/",
        "Disallow: /healthz/",
        "Disallow: /*?search=",
        "Disallow: /*?sort=",
        "Disallow: /*?per_page=",
        "Disallow: /*?variant=",
        "",
        f"Sitemap: {settings.SITE_URL.rstrip('/')}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
