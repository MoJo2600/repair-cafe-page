from datetime import date, timedelta

from app.extensions import db
from app.models import Repair


def _repair(datum, status):
    return Repair(datum=datum, geraet_art="Toaster", status=status, qr_token=f"t{id(datum)}{status}")


def test_timeline_groups_by_iso_week(helper_client):
    monday = date.today() - timedelta(days=date.today().weekday() + 14)
    db.session.add_all(
        [
            _repair(monday, "Offen"),
            _repair(monday + timedelta(days=6), "Repariert"),  # same ISO week (Sunday)
            _repair(monday + timedelta(days=7), "Nicht Repariert"),  # next week
        ]
    )
    db.session.commit()

    data = helper_client.get("/api/repairs/stats/timeline").get_json()["data"]

    assert len(data) == 2
    first, second = data
    iso_year, iso_week, _ = monday.isocalendar()
    assert first["week"] == f"{iso_year}-{iso_week:02d}"
    assert first["label"] == f"KW {iso_week} {iso_year}"
    assert (first["offen"], first["abgeschlossen"]) == (1, 1)
    assert second["nicht_repariert"] == 1
