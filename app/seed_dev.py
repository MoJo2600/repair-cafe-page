#!/usr/bin/env python
"""
Development seed script — populate the database with realistic test data.

Usage (from the app/ directory):
    python seed_dev.py

Safe to re-run: skips creation if data already exists (checks for the
sentinel admin user).  Pass --reset to wipe all seeded rows first.
"""

# ---------------------------------------------------------------------------
# Bootstrap Flask app context
# ---------------------------------------------------------------------------
import os
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

app_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(app_dir)
os.chdir(app_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import create_app

app = create_app()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _qr():
    return secrets.token_hex(16)


def _dt(days_ago=0, hour=10, minute=0):
    base = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------


def seed(reset=False):
    from werkzeug.security import generate_password_hash

    from app.extensions import db
    from app.models import Customer, Repair, RepairLog, User, VdeTest

    with app.app_context():
        if reset:
            print("Resetting seeded data …")
            VdeTest.query.delete()
            RepairLog.query.delete()
            Repair.query.delete()
            Customer.query.delete()
            User.query.delete()
            db.session.commit()
            print("  done.")

        # Guard: skip if hans.mueller already present
        if User.query.filter_by(username="hans.mueller").first():
            print("Seed data already present. Use --reset to re-seed.")
            return

        # ------------------------------------------------------------------
        # Users
        # ------------------------------------------------------------------
        admin = User(
            username="admin",
            vorname="Admin",
            nachname="User",
            email="admin@repaircafe.local",
            password_hash=generate_password_hash("admin123"),
            is_admin=True,
            is_active=True,
            created_at=_dt(30),
        )
        db.session.query(User).filter_by(
            username=admin.username
        ).delete()  # ensure idempotent
        hans = User(
            username="hans.mueller",
            vorname="Hans",
            nachname="Müller",
            email="hans@repaircafe.local",
            password_hash=generate_password_hash("test123"),
            is_admin=False,
            is_active=True,
            created_at=_dt(20),
        )
        erika = User(
            username="erika.schmidt",
            vorname="Erika",
            nachname="Schmidt",
            email="erika@repaircafe.local",
            password_hash=generate_password_hash("test123"),
            is_admin=False,
            is_active=True,
            created_at=_dt(20),
        )
        db.session.add_all([admin, hans, erika])
        db.session.flush()  # get IDs
        print(f"  Users: {admin.username}, {hans.username}, {erika.username}")

        # ------------------------------------------------------------------
        # Customers
        # ------------------------------------------------------------------
        kurt = Customer(
            vorname="Kurt",
            nachname="Wagner",
            telefon="0151-11223344",
            email="kurt@example.com",
            created_at=_dt(15),
        )
        maria = Customer(
            vorname="Maria",
            nachname="Hoffmann",
            telefon="0176-55667788",
            email=None,
            created_at=_dt(10),
        )
        peter = Customer(
            vorname="Peter",
            nachname="Klein",
            telefon="0170-99887766",
            created_at=_dt(8),
        )
        sabine = Customer(
            vorname="Sabine",
            nachname="Braun",
            telefon="0160-12345678",
            created_at=_dt(25),
        )
        georg = Customer(
            vorname="Georg",
            nachname="Fischer",
            created_at=_dt(2),
        )
        lisa = Customer(
            vorname="Lisa",
            nachname="Weber",
            telefon="0151-22334455",
            created_at=_dt(6),
        )
        db.session.add_all([kurt, maria, peter, sabine, georg, lisa])
        db.session.flush()
        print(
            f"  Customers: {kurt.vorname} {kurt.nachname}, {maria.vorname} {maria.nachname}, "
            f"{peter.vorname} {peter.nachname}, {sabine.vorname} {sabine.nachname}, "
            f"{georg.vorname} {georg.nachname}, {lisa.vorname} {lisa.nachname}"
        )

        # ------------------------------------------------------------------
        # Repairs
        # ------------------------------------------------------------------
        r1 = Repair(
            customer_id=kurt.id,
            datum=date.today() - timedelta(days=14),
            reparatur_art="Elektro",
            geraet_art="Staubsauger",
            defekt_besch="Saugt nicht mehr, Motor läuft aber",
            status="Repariert",
            user_id=hans.id,
            reparatur_dauer=45,
            reparatur_besch="Antriebsriemen gebrochen, ersetzt.",
            qr_token=_qr(),
        )
        r2 = Repair(
            customer_id=maria.id,
            datum=date.today() - timedelta(days=7),
            reparatur_art="Elektro",
            geraet_art="Tischlampe",
            defekt_besch="Leuchtet nicht mehr",
            status="In Bearbeitung",
            user_id=erika.id,
            qr_token=_qr(),
        )
        r3 = Repair(
            customer_id=peter.id,
            datum=date.today() - timedelta(days=3),
            reparatur_art="PC",
            geraet_art="Laptop",
            defekt_besch="Startet nicht, Akku defekt",
            status="Offen",
            qr_token=_qr(),
        )
        r4 = Repair(
            customer_id=sabine.id,
            datum=date.today() - timedelta(days=21),
            reparatur_art="Textil",
            geraet_art="Nähmaschine",
            defekt_besch="Stich unregelmäßig, Faden reißt",
            status="Nicht Repariert",
            status_detail="Nicht moeglich",
            user_id=erika.id,
            reparatur_dauer=30,
            qr_token=_qr(),
        )
        r5 = Repair(
            customer_id=georg.id,
            datum=date.today(),
            reparatur_art="Audio",
            geraet_art="Plattenspieler",
            defekt_besch="Dreht sich zu langsam",
            status="Offen",
            qr_token=_qr(),
        )
        r6 = Repair(
            customer_id=lisa.id,
            datum=date.today() - timedelta(days=5),
            reparatur_art="Elektro",
            geraet_art="Wasserkocher",
            defekt_besch="Schaltet nicht ab, Temperatursensor defekt",
            status="Repariert",
            user_id=hans.id,
            reparatur_dauer=20,
            din_pruef=True,
            qr_token=_qr(),
        )
        db.session.add_all([r1, r2, r3, r4, r5, r6])
        db.session.flush()
        print(f"  Repairs: {r1.id}, {r2.id}, {r3.id}, {r4.id}, {r5.id}, {r6.id}")

        # ------------------------------------------------------------------
        # Repair logs
        # ------------------------------------------------------------------
        db.session.add_all(
            [
                RepairLog(
                    repair_id=r1.id,
                    user_id=hans.id,
                    reparatur_dauer=20,
                    created_at=_dt(14, 10),
                    reparatur_besch="Erstdiagnose: Riemen gebrochen. Ersatzteil bestellt.",
                ),
                RepairLog(
                    repair_id=r1.id,
                    user_id=hans.id,
                    reparatur_dauer=25,
                    created_at=_dt(7, 14),
                    reparatur_besch="Riemen eingebaut, Testlauf erfolgreich.",
                ),
                RepairLog(
                    repair_id=r2.id,
                    user_id=erika.id,
                    reparatur_dauer=15,
                    created_at=_dt(7, 11),
                    reparatur_besch="Schalter defekt, Ersatz in Beschaffung.",
                ),
                RepairLog(
                    repair_id=r4.id,
                    user_id=erika.id,
                    reparatur_dauer=30,
                    created_at=_dt(21, 10),
                    reparatur_besch="Greifer-Timing geprüft, Ersatzteile nicht mehr verfügbar.",
                ),
                RepairLog(
                    repair_id=r6.id,
                    user_id=hans.id,
                    reparatur_dauer=20,
                    created_at=_dt(5, 9),
                    reparatur_besch="Bimetallschalter getauscht, Funktion geprüft.",
                ),
            ]
        )
        print("  RepairLogs added.")

        # ------------------------------------------------------------------
        # VDE test (for r6 — the kettle, which had din_pruef=True)
        # ------------------------------------------------------------------
        db.session.add(
            VdeTest(
                repair_id=r6.id,
                prufer_user_id=hans.id,
                prufer=f"{hans.vorname} {hans.nachname}",
                pruefgeraet_name="Benning ST 750",
                pruefgeraet_serial="SN-2024-001",
                schutzklasse="Schutzklasse I",
                sichtpruefung_gehaeuse=True,
                sichtpruefung_kabel=True,
                sichtpruefung_stecker=True,
                sichtpruefung_zugentlastung=True,
                sichtpruefung_sicherheit=True,
                schutzleiter_pruefung=True,
                isolationspruefung=True,
                ableitstrom_pruefung=True,
                gesamtergebnis=True,
                bemerkungen="Gerät nach Reparatur vollständig geprüft und freigegeben.",
                created_at=_dt(5, 10),
            )
        )
        print("  VdeTest added.")

        # ------------------------------------------------------------------
        # Commit
        # ------------------------------------------------------------------
        db.session.commit()
        print("\nDone! Test accounts:")
        print("  admin / admin123    (admin)")
        print("  hans.mueller / test123")
        print("  erika.schmidt / test123")

        # ------------------------------------------------------------------
        # Disclaimer sample
        # ------------------------------------------------------------------
        import shutil

        sample = Path(parent_dir) / "config" / "Disclaimer_sample.pdf"
        dest = Path(parent_dir) / "data" / "disclaimer.pdf"
        if sample.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sample, dest)
            print(f"\n  Disclaimer sample copied to {dest}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    reset = "--reset" in sys.argv
    seed(reset=reset)
