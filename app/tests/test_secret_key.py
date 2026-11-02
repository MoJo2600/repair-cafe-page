"""
Production startup refuses missing, placeholder or short FLASK_SECRET_KEY values.
"""

import pytest

from app import create_app
from app.config import BaseConfig


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    # create_app() writes FLASK_ENV; monkeypatch restores it afterwards.
    monkeypatch.setenv("FLASK_ENV", "development")


@pytest.mark.parametrize(
    "key", [None, "change_me_secret", "change_me" + "x" * 40, "too-short-secret"]
)
def test_production_rejects_weak_secret_key(monkeypatch, key):
    monkeypatch.setattr(BaseConfig, "SECRET_KEY", key)
    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        create_app("production")


def test_development_accepts_short_secret_key(monkeypatch):
    monkeypatch.setattr(BaseConfig, "SECRET_KEY", "dev")
    assert create_app("development").config["SECRET_KEY"] == "dev"
