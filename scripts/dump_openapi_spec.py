"""
Write the backend's OpenAPI (Swagger 2.0) spec to a file, without a running server
or database. The frontend client is generated from this file (pnpm generate-api).

Usage (from the project root):
    python scripts/dump_openapi_spec.py [output]   # default: frontend/openapi.json
"""

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Throwaway configuration, always overriding the environment so the script can never
# create tables or a default admin in a real database: in-memory DB, no OIDC, temp data
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["FLASK_SECRET_KEY"] = "spec-dump"
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="repaircafe-spec-")
os.environ["CREATE_TABLES_ON_STARTUP"] = "1"
for key in ("OIDC_ISSUER", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET", "PUBLIC_URL"):
    os.environ[key] = ""

from app import create_app  # noqa: E402


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "frontend" / "openapi.json"
    app = create_app("development")
    with app.test_client() as client:
        response = client.get("/apispec_1.json")
        if response.status_code != 200:
            sys.exit(f"Spec request failed: HTTP {response.status_code}")
        spec = response.get_json()

    # Host/version change per environment and release; keep the file stable
    spec.pop("host", None)
    spec.get("info", {}).pop("version", None)

    output.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
