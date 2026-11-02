"""
Cross-site request protection for state-changing /api requests.
"""

from urllib.parse import urlsplit

from flask import current_app, request


def same_origin_request() -> bool:
    """True if the request comes from this app's own origin.

    SameSite=Lax cookies are still sent by other apps under the same domain
    (e.g. wiki.repaircafe-hemau.de), so the session cookie alone does not
    prove that this app's frontend made the request."""
    origin = request.headers.get("Origin")
    if origin:
        source = urlsplit(origin)
        allowed = [urlsplit(request.host_url)]
        if current_app.config.get("PUBLIC_URL"):
            allowed.append(urlsplit(current_app.config["PUBLIC_URL"]))
        if not any(
            (source.scheme, source.netloc) == (target.scheme, target.netloc)
            for target in allowed
        ):
            request_origin = urlsplit(request.host_url)
            development_proxy = (
                current_app.debug
                and source.scheme == request_origin.scheme
                and source.hostname == request_origin.hostname
                and source.hostname in {"localhost", "127.0.0.1", "::1"}
            )
            if not development_proxy:
                return False
    return request.headers.get("Sec-Fetch-Site") != "cross-site"
