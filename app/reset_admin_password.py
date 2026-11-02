#!/usr/bin/env python
"""
Set the password of a local admin account (break-glass login).

Run inside the backend container, e.g. from the Dockge container shell:

    reset-admin-password                 # account "admin", password is prompted
    reset-admin-password --user NAME     # another local admin account
    reset-admin-password --generate      # print a random password instead

The account is (re)activated and created if it does not exist. SSO accounts
are refused. Nothing is written to the application log.
"""

import argparse
import getpass
import os
import secrets
import sys

# Put the project root on sys.path so 'app' can be imported; realpath because
# the image links this file to /usr/local/bin/reset-admin-password.
app_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.dirname(app_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from werkzeug.security import generate_password_hash  # noqa: E402

from app.extensions import db  # noqa: E402
from app.models import User  # noqa: E402

MIN_PASSWORD_LENGTH = 12


class ResetError(Exception):
    pass


def reset_admin_password(username: str, password: str) -> bool:
    """Set the password of local admin `username`; returns True if the account was created."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ResetError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    user = User.query.filter_by(username=username).first()
    created = user is None
    if created:
        user = User(
            username=username,
            vorname="Admin",
            nachname="",
            email=f"{username}@repaircafe.local",
            is_admin=True,
        )
        db.session.add(user)
    elif user.oidc_sub:
        raise ResetError(f"'{username}' is an SSO account; its password is managed by the identity provider")
    elif not user.is_admin:
        raise ResetError(f"'{username}' is not an admin account")

    user.password_hash = generate_password_hash(password)
    user.is_active = True
    db.session.commit()
    return created


def _prompt_password() -> str:
    password = getpass.getpass(f"New password (min. {MIN_PASSWORD_LENGTH} characters): ")
    if password != getpass.getpass("Repeat password: "):
        raise ResetError("Passwords do not match")
    return password


def run(argv: list[str] | None = None) -> int:
    """Command entry point; expects an active app context."""
    parser = argparse.ArgumentParser(
        prog="reset-admin-password",
        description="Set the password of a local admin account (break-glass login).",
    )
    parser.add_argument("--user", default="admin", help="local admin username (default: admin)")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="generate a random password and print it instead of prompting",
    )
    args = parser.parse_args(argv)

    try:
        if args.generate:
            password = secrets.token_urlsafe(18)
        elif sys.stdin.isatty():
            password = _prompt_password()
        else:
            raise ResetError("No terminal for the password prompt; use --generate")
        created = reset_admin_password(args.user, password)
    except ResetError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"{'Created' if created else 'Updated'} local admin account '{args.user}'.")
    if args.generate:
        print(f"New password: {password}")
        print("Store it in your password manager; it is not shown again.")
    return 0


if __name__ == "__main__":
    from app import create_app

    with create_app().app_context():
        sys.exit(run())
