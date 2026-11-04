"""
Celebration sound: everyone can fetch it, only admins can replace or reset it,
and only MP3 files are stored.
"""

import io

import pytest

from app.api.config import CELEBRATION_SOUND_MAX_BYTES
from app.tests.conftest import _make_user, login_as

URL = "/api/config/celebration-sound"
MP3_ID3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 64
MP3_FRAME = b"\xff\xfb\x90\x64" + b"\x00" * 64


@pytest.fixture
def admin_client(client, app):
    _make_user("testadmin", is_admin=True)
    return login_as(client, "testadmin")


def _upload(client, data, name="jubel.mp3"):
    return client.post(
        URL,
        data={"file": (io.BytesIO(data), name, "audio/mpeg")},
        content_type="multipart/form-data",
    )


def test_default_sound_is_public(client):
    resp = client.get(URL)
    assert resp.status_code == 200
    assert resp.mimetype == "audio/mpeg"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.data[:3] == b"ID3" or resp.data[0] == 0xFF


@pytest.mark.parametrize("data", [MP3_ID3, MP3_FRAME])
def test_admin_upload_replaces_and_reset_restores(admin_client, data):
    default = admin_client.get(URL).data
    assert _upload(admin_client, data).status_code == 200
    assert admin_client.get(URL).data == data

    assert admin_client.delete(URL).status_code == 200
    assert admin_client.get(URL).data == default


def test_non_mp3_is_rejected(admin_client):
    resp = _upload(admin_client, b"<html><script>alert(1)</script>", "jubel.mp3")
    assert resp.status_code == 400


def test_too_large_is_rejected(admin_client):
    resp = _upload(admin_client, MP3_ID3 + b"\x00" * CELEBRATION_SOUND_MAX_BYTES)
    assert resp.status_code == 400


def test_non_admin_cannot_change_sound(helper_client):
    assert _upload(helper_client, MP3_ID3).status_code == 403
    assert helper_client.delete(URL).status_code == 403
