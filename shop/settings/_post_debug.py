"""Продакшен-настройки cookie/HTTPS/HSTS при DEBUG=False (общие для local и prod)."""


def apply_production_security(env, ns: dict) -> None:
    if ns.get("DEBUG"):
        return
    ns["SESSION_COOKIE_SECURE"] = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=True)
    ns["CSRF_COOKIE_SECURE"] = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=True)
    ns["SECURE_SSL_REDIRECT"] = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)

    ns["SECURE_HSTS_SECONDS"] = env.int("DJANGO_SECURE_HSTS_SECONDS", default=0)
    ns["SECURE_HSTS_INCLUDE_SUBDOMAINS"] = env.bool(
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
    )
    ns["SECURE_HSTS_PRELOAD"] = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)

    ns["SECURE_CONTENT_TYPE_NOSNIFF"] = True
    ns["SECURE_REFERRER_POLICY"] = "same-origin"
