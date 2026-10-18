"""
Every /api endpoint must reject anonymous requests unless it is explicitly
marked @public_endpoint. A new endpoint without protection fails this test.
"""

import re

import pytest

# (endpoint name, method) pairs that are intentionally reachable without login.
PUBLIC = {
    ("health.healthcheck", "GET"),
    ("auth.api_login", "POST"),
    ("config.get_logo", "GET"),
    ("oidc.auth_config", "GET"),
    ("oidc.oidc_login", "GET"),
    ("oidc.oidc_callback", "GET"),
}


def _api_routes(app):
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/"):
            continue
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            # Fill URL parameters with a dummy value that satisfies int converters.
            url = re.sub(r"<(?:[^:>]+:)?[^>]+>", "1", rule.rule)
            yield rule.endpoint, method, url


def test_public_allowlist_matches_routes(app):
    routes = {(endpoint, method) for endpoint, method, _ in _api_routes(app)}
    assert PUBLIC <= routes, f"stale entries in PUBLIC: {PUBLIC - routes}"


def test_anonymous_requests_are_rejected(app, client):
    unprotected = []
    for endpoint, method, url in _api_routes(app):
        if (endpoint, method) in PUBLIC:
            continue
        try:
            resp = client.open(url, method=method, json={})
        except Exception as e:  # the handler ran, so it was reachable
            unprotected.append(f"{method} {url} -> raised {type(e).__name__}")
            continue
        if resp.status_code != 401:
            unprotected.append(f"{method} {url} -> {resp.status_code}")
    assert not unprotected, "endpoints reachable without login:\n" + "\n".join(unprotected)


@pytest.mark.parametrize("url", ["/api/healthz", "/api/config/logo"])
def test_public_endpoints_need_no_login(client, url):
    assert client.get(url).status_code != 401


def test_logged_in_user_can_list_repairs(helper_client):
    resp = helper_client.get("/api/list")
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "method,url",
    [("GET", "/api/export"), ("GET", "/api/mailexport"), ("POST", "/api/users")],
)
def test_admin_endpoints_reject_helpers(helper_client, method, url):
    assert helper_client.open(url, method=method, json={}).status_code == 403


def test_cors_disabled_by_default(client):
    resp = client.get("/api/healthz", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in resp.headers
