#!/usr/bin/env python3
"""
Import transcribed paper repair forms ("Reparaturzettel") through the REST API.

Input (semicolon-separated, UTF-8 CSV, e.g. edited in LibreOffice):
  repairs.csv    one row per repair; columns see REQUIRED_COLUMNS below
  repairers.csv  name;user_id;hinweis — maps handwritten repairer names to user IDs

For every row the script
  1. creates the repair (and customer) with POST /api/repairs, reusing an
     existing customer with the same name,
  2. uploads the scanned PDF as the signed disclaimer (Haftungsausschluss),
  3. sets unterschrift_haft,
  4. assigns the first repairer, adds one work log per repairer (duration on
     the first) and moves the repair to its final status.

Progress is kept in manifest.csv next to repairs.csv, so a rerun resumes
where it stopped. Afterwards it writes fix_dates.sql: the API stamps
closed_at, log and customer timestamps with the import time; the SQL resets
them to the repair date for the imported records only.

Usage:
  export RC_URL=https://reparaturen.example.org RC_USER=admin RC_PASSWORD=...
  python3 scripts/import_paper_forms.py --check          # validate only
  python3 scripts/import_paper_forms.py --limit 1        # import one row
  python3 scripts/import_paper_forms.py                  # import the rest

RC_USER must be a local password account (with SSO enabled: a local admin).

Behind Cloudflare Access, additionally set one of:
  RC_CF_AUTHORIZATION=<value of the CF_Authorization cookie from a browser
                       that is logged in to the site>
  RC_CF_ACCESS_CLIENT_ID=... RC_CF_ACCESS_CLIENT_SECRET=...   (service token)
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import requests

REQUIRED_COLUMNS = [
    "pdf_file", "datum", "vorname", "nachname", "telefon", "email", "kategorie",
    "geraet_art", "defekt_besch", "ergebnis", "status_detail", "reparatur_besch",
    "din_pruef", "reparateure_raw", "reparateure", "dauer_min",
    "haftung_unterschrieben", "unsicher", "notiz",
]
STATUS_DETAILS = {
    "Offen": set(),
    "Repariert": set(),
    "Nicht Repariert": {"Nicht moeglich", "Abbruch", "Wartezeit zu lang"},
}
CLOSED = {"Repariert", "Nicht Repariert"}
FALLBACK_BESCH = "Übernommen aus Papierzettel"
STEPS = ["created", "disclaimer", "haftung", "assigned", "logs", "done"]
YES = {"ja", "j", "yes", "y", "true", "1", "x"}
NO = {"nein", "n", "no", "false", "0", ""}


# ── CSV helpers ─────────────────────────────────────────────────────────────

def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        return [
            {k.strip(): (v or "").strip() for k, v in row.items() if k}
            for row in csv.DictReader(f, delimiter=delimiter)
        ]


def parse_date(value: str) -> date:
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Datum '{value}' nicht lesbar (TT.MM.JJJJ)")


def parse_bool(value: str, field: str) -> bool:
    v = value.lower()
    if v in YES:
        return True
    if v in NO:
        return False
    raise ValueError(f"{field}: '{value}' ist weder ja noch nein")


def split_names(value: str) -> list[str]:
    return [n.strip() for n in re.split(r"[,;/&]", value) if n.strip()]


def row_keys(rows: list[dict]) -> list[str]:
    """Stable key per row: PDF name plus occurrence (a form can hold 2 devices)."""
    seen: dict[str, int] = {}
    keys = []
    for r in rows:
        seen[r["pdf_file"]] = seen.get(r["pdf_file"], 0) + 1
        keys.append(f"{r['pdf_file']}#{seen[r['pdf_file']]}")
    return keys


class Manifest:
    FIELDS = ["key", "repair_id", "step", "new_customer_id"]

    def __init__(self, path: Path):
        self.path = path
        self.rows: dict[str, dict] = {}
        if path.exists():
            for r in read_csv(path):
                self.rows[r["key"]] = r

    def get(self, key: str) -> dict:
        return self.rows.get(key, {"key": key, "repair_id": "", "step": "", "new_customer_id": ""})

    def save(self, entry: dict) -> None:
        self.rows[entry["key"]] = entry
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self.FIELDS, delimiter=";")
            w.writeheader()
            w.writerows(self.rows.values())
        tmp.replace(self.path)


# ── API client ──────────────────────────────────────────────────────────────

class Api:
    """Session-based client. Redirects are never followed: a redirect from an
    API endpoint means a proxy (e.g. Cloudflare Access) or a wrong URL."""

    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/") + "/api"
        self.s = requests.Session()
        # Cloudflare Access in front of the app: either a service token
        # (Zero Trust → Access → Service Auth) or the CF_Authorization cookie
        # copied from a logged-in browser.
        cf_id = os.environ.get("RC_CF_ACCESS_CLIENT_ID")
        cf_secret = os.environ.get("RC_CF_ACCESS_CLIENT_SECRET")
        if cf_id and cf_secret:
            self.s.headers.update({"CF-Access-Client-Id": cf_id,
                                   "CF-Access-Client-Secret": cf_secret})
        cf_cookie = os.environ.get("RC_CF_AUTHORIZATION")
        if cf_cookie:
            host = requests.utils.urlparse(base_url).hostname
            self.s.cookies.set("CF_Authorization", cf_cookie, domain=host)

    def _check(self, resp: requests.Response, what: str) -> dict:
        if resp.is_redirect:
            location = resp.headers.get("Location", "")
            hint = ("Cloudflare Access blockiert den Zugriff: RC_CF_AUTHORIZATION oder "
                    "RC_CF_ACCESS_CLIENT_ID/_SECRET setzen (siehe --help)."
                    if "cloudflareaccess.com" in location
                    else "RC_URL prüfen (https, ohne /api).")
            raise RuntimeError(f"{what}: Weiterleitung (HTTP {resp.status_code}) nach "
                               f"{location[:120]} — {hint}")
        if resp.status_code >= 400:
            raise RuntimeError(f"{what}: HTTP {resp.status_code} {resp.text[:300]}")
        if not resp.content:
            return {}
        if "json" not in resp.headers.get("Content-Type", ""):
            raise RuntimeError(f"{what}: keine JSON-Antwort (HTTP {resp.status_code}, "
                               f"{resp.headers.get('Content-Type')}): {resp.text[:200]!r}")
        return resp.json()

    def _req(self, method: str, path: str, what: str, **kw) -> dict:
        r = self.s.request(method, f"{self.base}{path}", allow_redirects=False, timeout=60, **kw)
        return self._check(r, what)

    def login(self, user: str, password: str) -> None:
        self._req("POST", "/auth/login", "Login", json={"username": user, "password": password})

    def get(self, path: str, **params):
        return self._req("GET", path, f"GET {path}", params=params)

    def post(self, path: str, payload: dict):
        return self._req("POST", path, f"POST {path}", json=payload)

    def put(self, path: str, payload: dict):
        return self._req("PUT", path, f"PUT {path}", json=payload)

    def upload_pdf(self, path: str, pdf: Path):
        with pdf.open("rb") as f:
            return self._req("POST", path, f"POST {path}",
                             files={"file": (pdf.name, f, "application/pdf")})


# ── Validation ──────────────────────────────────────────────────────────────

def validate(rows, keys, repairer_map, repair_types, user_ids, pdf_dir):
    """Return (errors, warnings, prepared rows)."""
    errors, warnings, prepared = [], [], []
    for n, (row, key) in enumerate(zip(rows, keys), start=2):  # line 1 = header
        where = f"Zeile {n} ({key})"
        missing = [c for c in REQUIRED_COLUMNS if c not in row]
        if missing:
            errors.append(f"{where}: Spalten fehlen: {', '.join(missing)}")
            continue
        p: dict = {"key": key, "line": n}
        try:
            p["datum"] = parse_date(row["datum"]) if row["datum"] else None
            if not p["datum"]:
                errors.append(f"{where}: datum fehlt")
            p["haftung"] = parse_bool(row["haftung_unterschrieben"], "haftung_unterschrieben")
            p["din_pruef"] = parse_bool(row["din_pruef"], "din_pruef")
            p["dauer"] = int(row["dauer_min"]) if row["dauer_min"] else 0
        except ValueError as e:
            errors.append(f"{where}: {e}")
            continue

        for field in ("vorname", "nachname"):
            if not row[field]:
                errors.append(f"{where}: {field} fehlt (ggf. '-' eintragen)")
        if not row["geraet_art"]:
            errors.append(f"{where}: geraet_art fehlt (ggf. 'Unbekannt')")
        for field, limit in (("geraet_art", 100), ("defekt_besch", 400), ("reparatur_besch", 400),
                             ("telefon", 40), ("email", 100), ("vorname", 100), ("nachname", 100)):
            if len(row[field]) > limit:
                errors.append(f"{where}: {field} länger als {limit} Zeichen")
        if row["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", row["email"]):
            errors.append(f"{where}: email ungültig")

        rt = repair_types.get(row["kategorie"].lower())
        if rt is None:
            errors.append(f"{where}: kategorie '{row['kategorie']}' unbekannt "
                          f"(erlaubt: {', '.join(sorted(repair_types))})")
        p["repair_type_id"] = rt

        ergebnis = row["ergebnis"]
        if ergebnis not in STATUS_DETAILS:
            errors.append(f"{where}: ergebnis muss Repariert, Nicht Repariert oder Offen sein")
        elif row["status_detail"] and row["status_detail"] not in STATUS_DETAILS[ergebnis]:
            errors.append(f"{where}: status_detail '{row['status_detail']}' passt nicht zu {ergebnis}")
        elif ergebnis == "Nicht Repariert" and not row["status_detail"]:
            errors.append(f"{where}: Nicht Repariert braucht status_detail "
                          "(Nicht moeglich / Abbruch / Wartezeit zu lang)")

        users = []
        names = split_names(row["reparateure"])
        for name in names:
            uid = repairer_map.get(name.lower())
            if uid is None:
                errors.append(f"{where}: Reparateur '{name}' hat keine user_id in repairers.csv")
            elif user_ids is not None and uid not in user_ids:
                errors.append(f"{where}: user_id {uid} ({name}) existiert nicht")
            elif uid not in users:
                users.append(uid)
        p["users"] = users
        if ergebnis in CLOSED and not names:
            errors.append(f"{where}: abgeschlossene Reparatur braucht mindestens einen Reparateur")

        p["reparatur_besch"] = row["reparatur_besch"]
        if ergebnis in CLOSED and not p["reparatur_besch"]:
            p["reparatur_besch"] = FALLBACK_BESCH
            warnings.append(f"{where}: reparatur_besch leer → '{FALLBACK_BESCH}'")

        pdf = pdf_dir / row["pdf_file"]
        if not pdf.is_file():
            errors.append(f"{where}: PDF {pdf} nicht gefunden")
        elif pdf.read_bytes()[:4] != b"%PDF":
            errors.append(f"{where}: {pdf.name} ist keine PDF-Datei")
        p["pdf"] = pdf

        if row["unsicher"]:
            errors.append(f"{where}: Spalte 'unsicher' ist nicht leer ({row['unsicher']}) — "
                          "prüfen und leeren")
        p["row"] = row
        prepared.append(p)
    return errors, warnings, prepared


# ── Import ──────────────────────────────────────────────────────────────────

def find_customer(api: Api, cache: dict, row: dict) -> int | None:
    name_key = (row["vorname"].lower(), row["nachname"].lower())
    if name_key in cache:
        return cache[name_key]
    hits = api.get("/customers/search", q=row["nachname"]).get("data", [])
    exact = [c for c in hits
             if (c.get("vorname") or "").lower() == name_key[0]
             and (c.get("nachname") or "").lower() == name_key[1]]
    if not exact:
        return None
    digits = re.sub(r"\D", "", row["telefon"])
    for c in exact:
        if digits and digits[-6:] in re.sub(r"\D", "", c.get("telefon") or ""):
            cache[name_key] = c["id"]
            return c["id"]
    cache[name_key] = exact[0]["id"]
    return exact[0]["id"]


def import_row(api: Api, p: dict, manifest: Manifest, customers: dict) -> None:
    row, entry = p["row"], manifest.get(p["key"])
    step = entry["step"]
    done = STEPS.index(step) + 1 if step else 0
    rid = entry["repair_id"]

    if done <= STEPS.index("created"):
        customer_id = find_customer(api, customers, row)
        payload = {
            "datum": p["datum"].isoformat(),
            "geraet_art": row["geraet_art"],
            "repair_type_id": p["repair_type_id"],
            "vorname": row["vorname"],
            "nachname": row["nachname"],
            "telefon": row["telefon"] or None,
            "email": row["email"] or None,
            "defekt_besch": row["defekt_besch"] or None,
        }
        if customer_id:
            payload["customer_id"] = customer_id
        res = api.post("/repairs", payload)
        rid = str(res["id"])
        new_cid = res.get("data", {}).get("customer_id")
        customers[(row["vorname"].lower(), row["nachname"].lower())] = new_cid
        entry.update(repair_id=rid, step="created",
                     new_customer_id="" if customer_id else str(new_cid or ""))
        manifest.save(entry)

    if done <= STEPS.index("disclaimer"):
        api.upload_pdf(f"/repairs/{rid}/disclaimer", p["pdf"])
        entry["step"] = "disclaimer"
        manifest.save(entry)

    if done <= STEPS.index("haftung"):
        api.put(f"/repairs/{rid}", {"unterschrift_haft": p["haftung"], "din_pruef": p["din_pruef"]})
        entry["step"] = "haftung"
        manifest.save(entry)

    users = p["users"]
    if done <= STEPS.index("assigned"):
        if row["ergebnis"] in CLOSED:
            api.put(f"/repairs/{rid}", {"status": "In Bearbeitung", "user_id": users[0]})
        elif users:
            api.put(f"/repairs/{rid}", {"user_id": users[0]})
        entry["step"] = "assigned"
        manifest.save(entry)

    if done <= STEPS.index("logs"):
        text = p["reparatur_besch"] or row["defekt_besch"] or FALLBACK_BESCH
        for i, uid in enumerate(users):
            besch = text
            if i == 0 and row["reparateure_raw"]:
                besch = f"{text} [Papierzettel – Repariert von: {row['reparateure_raw']}]"
            api.post(f"/repairs/{rid}/logs", {
                "repair_id": int(rid),
                "user_id": uid,
                "reparatur_dauer": p["dauer"] if i == 0 else 0,
                "reparatur_besch": besch[:400],
            })
        entry["step"] = "logs"
        manifest.save(entry)

    if done <= STEPS.index("done"):
        if row["ergebnis"] in CLOSED:
            payload = {"status": row["ergebnis"], "reparatur_besch": p["reparatur_besch"]}
            if row["status_detail"]:
                payload["status_detail"] = row["status_detail"]
            api.put(f"/repairs/{rid}", payload)
        entry["step"] = "done"
        manifest.save(entry)


def write_fix_sql(manifest: Manifest, path: Path) -> None:
    ids = sorted(int(e["repair_id"]) for e in manifest.rows.values() if e["repair_id"])
    cids = sorted({int(e["new_customer_id"]) for e in manifest.rows.values() if e["new_customer_id"]})
    if not ids:
        return
    id_list = ", ".join(map(str, ids))
    sql = [
        "-- Generated by scripts/import_paper_forms.py.",
        "-- Resets timestamps the API set to the import time back to the repair date,",
        "-- for the imported repairs only.",
        "",
        "UPDATE repair_logs rl JOIN repairs r ON r.id = rl.repair_id",
        "SET rl.created_at = CAST(r.datum AS DATETIME)",
        f"WHERE r.id IN ({id_list});",
        "",
        "UPDATE repairs SET closed_at = CAST(datum AS DATETIME)",
        f"WHERE closed_at IS NOT NULL AND id IN ({id_list});",
    ]
    if cids:
        sql += [
            "",
            "UPDATE customers c JOIN (",
            f"  SELECT customer_id, MIN(datum) AS d FROM repairs WHERE id IN ({id_list})",
            "  GROUP BY customer_id) x ON x.customer_id = c.id",
            "SET c.created_at = CAST(x.d AS DATETIME)",
            f"WHERE c.id IN ({', '.join(map(str, cids))});",
        ]
    path.write_text("\n".join(sql) + "\n", encoding="utf-8")
    print(f"→ {path} geschrieben ({len(ids)} Reparaturen). Ausführen mit:")
    print(f"  docker compose exec -T db sh -c 'mariadb -u root -p\"$MYSQL_ROOT_PASSWORD\" "
          f"\"$MYSQL_DATABASE\"' < {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, default=Path("tmp/import/repairs.csv"))
    ap.add_argument("--repairers", type=Path, default=Path("tmp/import/repairers.csv"))
    ap.add_argument("--pdf-dir", type=Path, default=Path("tmp"))
    ap.add_argument("--check", action="store_true", help="only validate, write nothing")
    ap.add_argument("--offline", action="store_true",
                    help="with --check: skip server lookups (categories/users not verified)")
    ap.add_argument("--limit", type=int, default=0, help="import at most N not yet finished rows")
    args = ap.parse_args()

    rows = read_csv(args.csv)
    keys = row_keys(rows)
    repairer_map = {}
    for r in read_csv(args.repairers):
        if r.get("user_id"):
            repairer_map[r["name"].lower()] = int(r["user_id"])

    api = None
    if args.offline:
        repair_types = {k: 0 for k in ("audio", "elektro", "fahrrad", "möbel", "pc", "spielzeug",
                                       "schleifarbeiten", "telekom", "textil", "video", "sonstiges")}
        user_ids = None
    else:
        url, user, pw = (os.environ.get(k) for k in ("RC_URL", "RC_USER", "RC_PASSWORD"))
        if not (url and user and pw):
            print("RC_URL, RC_USER und RC_PASSWORD setzen (oder --check --offline).", file=sys.stderr)
            return 2
        api = Api(url)
        try:
            api.login(user, pw)
            settings = api.get("/settings")
            users = api.get("/users").get("data", [])
        except (RuntimeError, requests.RequestException) as e:
            print(f"FEHLER {e}", file=sys.stderr)
            return 2
        repair_types = {s["name"].lower(): s["id"] for s in settings.get("repair_type", [])}
        user_ids = {u["id"] for u in users}

    errors, warnings, prepared = validate(rows, keys, repairer_map, repair_types, user_ids, args.pdf_dir)
    for w in warnings:
        print("WARNUNG", w)
    for e in errors:
        print("FEHLER ", e)
    print(f"{len(prepared)} Zeilen gelesen, {len(errors)} Fehler, {len(warnings)} Warnungen.")
    if errors:
        return 1
    if args.check:
        return 0

    manifest = Manifest(args.csv.with_name("manifest.csv"))
    customers: dict = {}
    todo = [p for p in prepared if manifest.get(p["key"])["step"] != "done"]
    if args.limit:
        todo = todo[: args.limit]
    for p in todo:
        try:
            import_row(api, p, manifest, customers)
            print(f"OK     Zeile {p['line']} → Reparatur {manifest.get(p['key'])['repair_id']}")
        except Exception as e:  # stop on the first failure; rerun resumes
            print(f"FEHLER Zeile {p['line']} ({p['key']}): {e}", file=sys.stderr)
            write_fix_sql(manifest, args.csv.with_name("fix_dates.sql"))
            return 1
    write_fix_sql(manifest, args.csv.with_name("fix_dates.sql"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
