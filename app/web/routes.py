"""
Data API routes — statistics, exports, PDF generation, and e-mail delivery.
Registered with the /api prefix in the application factory.
"""

import json
import os

import pandas as pd
from flask import Blueprint, Response, current_app, send_file, send_from_directory

from app.models import Repair

web_bp = Blueprint("web", __name__)


@web_bp.route("/stat-data/<type>", methods=["GET"])
def stat_data(type):
    """
    Get statistics data for charts
    ---
    tags:
      - Data
    operationId: getStatData
    parameters:
      - name: type
        in: path
        required: true
        type: string
        enum: [repairs, devices, time]
    responses:
      200:
        description: Statistics data as JSON array
    """
    repairs = Repair.query.all()
    repairs_data = [repair.to_dict() for repair in repairs]
    df = pd.DataFrame(repairs_data)

    if df.empty:
        return json.dumps([])

    if type == "repairs":
        df["datum"] = pd.to_datetime(df["datum"])
        df["month"] = df["datum"].dt.to_period("M").dt.strftime("%Y-%m")
        df["success"] = (df["status"] == "Repariert").astype(int)
        df["failed"] = (df["status"] == "Nicht Repariert").astype(int)
        df = df.groupby("month").agg({"success": "sum", "failed": "sum"}).reset_index()
        return json.dumps(df.to_dict(orient="records"))

    if type == "devices":
        df = df.groupby("repair_type_name").size().reset_index(name="count")
        data = [
            {"name": row["repair_type_name"], "value": row["count"]}
            for _, row in df.iterrows()
        ]
        return json.dumps(data)

    if type == "time":
        df = (
            df.groupby(["repair_type_name", "status"])
            .agg({"reparatur_dauer": "sum"})
            .reset_index()
        )
        data = []
        for device, group in df.groupby("repair_type_name"):
            device_data = {"name": device, "children": []}
            for status, sub_group in group.groupby("status"):
                status_name = {"Repariert": "success", "Nicht Repariert": "failed"}.get(
                    status, "open"
                )
                status_data = {"name": status_name, "children": []}
                for duration, _ in sub_group.groupby("reparatur_dauer"):
                    status_data["children"].append(
                        {"name": str(duration), "value": duration}
                    )
                device_data["children"].append(status_data)
            data.append(device_data)
        return json.dumps(data)

    return json.dumps([])


@web_bp.route("/export", methods=["GET"])
def export():
    """Export all repairs to an Excel file (XLSX download)."""
    repairs_data = [r.to_dict() for r in Repair.query.all()]
    df = pd.DataFrame(repairs_data)
    filename = "export.xlsx"
    df.to_excel(filename, index=False)
    return send_from_directory(os.getcwd(), filename, as_attachment=True)


@web_bp.route("/createDisclaimer/<id>", methods=["GET"])
def create_disclaimer(id):
    """Generate and download a signed disclaimer PDF for a repair record."""
    from app.services.pdf_service import PDFService

    try:
        repair = Repair.query.get_or_404(id)
        data = repair.to_dict()

        pdf_service = PDFService()
        signed_pdf_stream = pdf_service.get_signed_pdf(
            data["unterschrift"], data["datum"]
        )

        if signed_pdf_stream:
            signed_pdf_stream.seek(0)
            return send_file(
                signed_pdf_stream,
                as_attachment=True,
                download_name=f"Haftungsausschluss_{id}_{data['datum']}.pdf",
                mimetype="application/pdf",
            )
        return Response(
            json.dumps({"reply": "error", "error": "Failed to create PDF"}),
            status=500,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"createDisclaimer error: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@web_bp.route("/mailexport", methods=["GET"])
def send_mail_export():
    """Trigger a CSV export e-mail to the configured recipient."""
    from app.services.email_service import EmailService
    from app.services.export_service import ExportService

    if not current_app.config["EMAIL_ENABLED"]:
        return Response(
            json.dumps({"reply": "error", "error": "E-Mail versandt ist deaktiviert."}),
            status=400,
            mimetype="application/json",
        )

    email_service = EmailService(current_app.config)
    export_service = ExportService()
    repairs = Repair.query.all()
    csv_data = export_service.repairs_to_csv(repairs)
    result = email_service.send_export_email(csv_data, filename_prefix="repairs_export")
    return json.dumps(result)
