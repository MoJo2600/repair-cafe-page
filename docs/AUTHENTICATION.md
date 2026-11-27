# Authentication

Everyone logs in with a primary login — a local password or SSO. On shared workshop
PCs, helpers then switch the logged-in session to themselves with a six-digit PIN.
Variable reference: [CONFIGURATION.md](CONFIGURATION.md#login-oidc--sso).

## Accounts and roles

| Role | Can |
|---|---|
| Helper (Reparateur) | everything around repairs, customers, logs, VDE tests, labels; own profile and PIN |
| Admin | additionally: users, settings, templates, deleting repairs and customers, export, style guide |

Accounts are either **local** (username + password, managed under **Benutzer**) or
**SSO** (created on first SSO login, linked by the OIDC subject).

On the first start an admin `admin` with a random password is created (printed to the
backend log). Reset: [DEPLOYMENT.md](DEPLOYMENT.md#admin-password-reset).

Sessions are HTTP-only cookies (`SameSite=Lax`). State-changing API requests from
other origins are rejected.

## Local login

Without OIDC settings everyone logs in with username and password. Failed attempts
are limited per IP and per username (`LOGIN_MAX_*`).

## SSO (OIDC)

Any provider with discovery and the authorization code flow works (tested with
Authentik).

1. Register an OIDC application at the provider with the redirect URI
   `<PUBLIC_URL>/api/auth/oidc/callback`.
2. Set `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `PUBLIC_URL`.
3. Use HTTPS and `SESSION_COOKIE_SECURE=true`.

While SSO is enabled, password login is only available to **local admins** as a
break-glass option.

Login requests fresh authentication (`prompt=login`), so on a shared PC the next person
cannot reuse the previous person's provider session. Requests that already passed
Cloudflare Access (header `Cf-Access-Jwt-Assertion`) skip this and reuse the provider
session, so there is only one login from outside.

### Claims

Claim names refer to top-level claims. Set an optional mapping to empty to disable it.
`sub`, `email`, `name` and `preferred_username` have their usual meaning.

| Claim | Effect |
|---|---|
| `OIDC_ADMIN_CLAIM` | admin if boolean `true` or the string `"true"`; any other value means non-admin. Synchronized on every login |
| `OIDC_GROUPS_CLAIM` + `OIDC_DENIED_GROUPS` | login refused if the user is in a denied group (deny-list; empty = no restriction) |
| `OIDC_PIN_CLAIM` | the user's PIN, only with `PIN_MODE=oidc` |

If the admin or PIN claim is **missing** from the token (usually because its scope is
not in `OIDC_SCOPES`), the stored admin flag and PIN are kept and a warning is logged.
A PIN claim that is present but empty or invalid removes the stored PIN.

Switching to a different issuer for an existing database needs a deliberate account
migration: subjects are not re-linked across issuers.

### Example: easyVerein via Authentik

```dotenv
PIN_MODE=oidc
OIDC_SCOPES=openid email profile repaircafe
OIDC_PIN_CLAIM=door_code
OIDC_ADMIN_CLAIM=repaircafe_admin
OIDC_GROUPS_CLAIM=groups
OIDC_DENIED_GROUPS=Kind
```

For a standard provider without a PIN claim use `PIN_MODE=local` with the default
scopes.

## PINs

Each user can have one six-digit PIN (leading zeros allowed). PINs are unique and
stored only as hashes keyed with `FLASK_SECRET_KEY` — never in plain text, never in
user lists or profile data. Keep the secret key stable: changing it invalidates all
PINs.

There are two deployment-wide modes; exactly one is active.

**`PIN_MODE=local`** — users open their profile (their name in the sidebar) and
generate a PIN. It is shown once and cannot be retrieved later; a forgotten PIN is
replaced, with confirmation. Nothing is generated automatically. Provider PIN claims
are ignored.

**`PIN_MODE=oidc`** — the PIN comes from `OIDC_PIN_CLAIM` and is refreshed on every
SSO login. Generating PINs in the profile (and through the API) is disabled; users look
up their PIN at the provider (e.g. their easyVerein profile). If a provider reassigns a
PIN, it is removed from its previous holder. There is no local fallback.

### Switching PIN mode

**Switching deletes all stored PINs.** Back up the database and stop all backend
instances first. The backend refuses to start until the exact transition is
acknowledged:

```dotenv
PIN_MODE=local
PIN_MODE_RESET_ACK=oidc-to-local      # or local-to-oidc
```

Start the backend, then remove `PIN_MODE_RESET_ACK`. The reset happens once and
atomically; later restarts do not delete new PINs. Accounts and sessions are kept.
Local users generate new PINs; provider PINs return at the next SSO login. Don't run
old-mode and new-mode backends at the same time — PIN operations fail while the
stored mode differs from the configuration.

## PIN lock and unlock

On a shared PC the session locks itself after **60 seconds** without activity (or
with the lock button). The lock screen shows a dashboard and a PIN keypad. Entering
any active helper's PIN switches the session to that helper; the primary login stays.
Auto-lock can be switched off per browser session, e.g. on a personal device.

Because the PIN may also be a member's door code, lock and unlock are only offered
**inside the workshop network**. Requests that come through Cloudflare (headers
`Cf-Ray`, `Cf-Connecting-Ip` or `Cf-Access-Jwt-Assertion`) get no lock button, no idle
lock and no PIN unlock. A session that was locked in the workshop and is then opened
from outside must log in again.

Wrong PINs are limited (`PIN_MAX_*`):

- per browser session: logged out after 5 wrong PINs, with a 60 s pause after every 3,
- per primary login account: 5 within 15 minutes, across all its browsers,
- globally: 15 within 15 minutes, then PIN unlock pauses for everyone.

While a limit applies, even a correct PIN is rejected. The primary login keeps
working.
