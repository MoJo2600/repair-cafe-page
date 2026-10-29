# Feature Ideas (post-MVP backlog)

Collected 2026-10-18 during a project analysis. Not scheduled — revisit after the MVP is live.
Roughly ordered by value for a repair café.

## 1. Events / sessions
Add an `Event` entity (date, location, team on duty) and link repairs to it.
Enables per-event statistics, volunteer sign-up per event, and is the foundation
for several ideas below (impact stats, queue, pre-registration).
Today a repair only has `datum`, so "everything from the café on 12 October" is just a date filter.

## 2. Environmental impact statistics
Estimate kg of waste avoided and CO₂ saved per device category.
Add an export in the Open Repair Data Standard (ORDS) format, used by the
Open Repair Alliance and Repair Café International — useful for funding applications and press.

## 3. Customer notifications
E-mail the customer when a repair is finished or waiting for a spare part.
`app/services/email_service.py` already exists but is barely used.

## 4. Waiting queue / public display
Hand out a queue number at check-in and show a "Now being served" screen at the venue.
Builds on the existing QR codes.

## 5. Spare parts & follow-up appointments
New "waiting for part" status, parts list (ordered by whom, cost),
reminders for devices that need a second visit.

## 6. Repair knowledge base
Add brand and model fields to `Repair`; let repairers search past repairs
("What fixed this coffee machine last time?").

## 7. Online pre-registration
Customers register their device and sign the liability waiver before the event,
shortening intake on the day.

## 8. Proper export
Real XLSX/CSV downloads from the UI, filterable by event, date range and status.
(README currently claims XLSX; `ExportService` only produces CSV via the legacy `app/web/routes.py`.)
