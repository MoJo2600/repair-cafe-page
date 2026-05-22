"""
Web pages routes blueprint.
Handles HTML page rendering for the repair cafe application.
"""

import json
import os

import flask_login
import pandas as pd
from flask import (
    Blueprint,
    Response,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from app.extensions import db
from app.models import Repair, Setting

web_bp = Blueprint("web", __name__)


@web_bp.route("/favicon.ico")
def favicon():
    """Serve favicon."""
    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@web_bp.route("/apple-touch-icon.png")
@web_bp.route("/apple-touch-icon-precomposed.png")
def appleicons():
    """Serve Apple touch icons."""
    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "appleicon.png",
        mimetype="image/png",
    )


@web_bp.route("/", methods=["GET"])
def root():
    """Redirect to index page."""
    return redirect(url_for("web.index"))


@web_bp.route("/index", methods=["GET"])
def index():
    """
    Root for Webpage. Renders index.html
    ---
    tags:
      - Web Pages
    operationId: indexPage
    responses:
      200:
        description: Main page
    """
    version = current_app.config.get("VERSION", "unknown")
    annotation = current_app.config.get("ANNOTATION", "")
    dropdown_art = [
        s.name
        for s in Setting.query.filter_by(category="repair_type", is_active=True)
        .order_by(Setting.sort_order, Setting.name)
        .all()
    ]
    return render_template(
        "index.html",
        annotation=annotation,
        version=version,
        dropdown_art=dropdown_art,
    )


@web_bp.route("/vue")
def vue_app():
    """
    Serve the Vue.js application
    ---
    tags:
      - Web Pages
    operationId: vueApp
    responses:
      200:
        description: Vue.js application
    """
    version = current_app.config.get("VERSION", "unknown")
    return render_template("vue_app.html", version=version)


@web_bp.route("/list", methods=["GET"])
def list_repairs():
    """
    Display all repairs in a table format
    ---
    tags:
      - Web Pages
    operationId: listRepairs
    responses:
      200:
        description: HTML page displaying all repairs in a table
      500:
        description: Internal Server Error - database query failed
    """
    try:
        repairs = Repair.query.all()
        repairs_list = [repair.to_dict() for repair in repairs]
        version = current_app.config.get("VERSION", "unknown")
        return render_template("list.html", repairs=repairs_list, version=version)
    except Exception as e:
        current_app.logger.error(f"Error in /list endpoint: {e}", exc_info=True)
        try:
            current_app.loki.error({"Message": "List page DB error", "Error": str(e)})  # type: ignore
        except Exception:
            pass
        version = current_app.config.get("VERSION", "unknown")
        return Response(
            render_template("list.html", repairs=[], version=version, error=str(e)),
            status=500,
        )


@web_bp.route("/edit/<id>", methods=["GET"])
def edit(id):
    """
    Edit page for a repair record
    ---
    tags:
      - Web Pages
    operationId: editRepair
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Edit page
    """
    try:
        config_mode = "dev" if current_app.config.get("DEBUG") else "prod"
        if config_mode == "dev":
            data = current_app.config["TEST_ROW"]
        else:
            repair = Repair.query.get_or_404(id)
            data = repair.to_dict()

        return render_template(
            "edit.html",
            row=data,
            dropdown_art=[
                s.name
                for s in Setting.query.filter_by(category="repair_type", is_active=True)
                .order_by(Setting.sort_order, Setting.name)
                .all()
            ],
            dropdown_erg=[],
            dropdown_who=[
                s.name
                for s in Setting.query.filter_by(category="repairer", is_active=True)
                .order_by(Setting.sort_order, Setting.name)
                .all()
            ],
        )
    except Exception as e:
        return json.dumps({"reply": "error", "error": str(e)})


@web_bp.route("/edit/<id>/<token>", methods=["GET"])
def edit_with_token(id, token):
    """
    Edit page for a repair record with token authentication
    ---
    tags:
      - Web Pages
    operationId: editRepairWithToken
    parameters:
      - name: id
        in: path
        required: true
        type: integer
      - name: token
        in: path
        required: true
        type: string
    responses:
      200:
        description: Edit page
      403:
        description: Invalid token
    """
    try:
        config_mode = "dev" if current_app.config.get("DEBUG") else "prod"
        if config_mode == "dev":
            data = current_app.config["TEST_ROW"]
        else:
            repair = Repair.query.get_or_404(id)
            data = repair.to_dict()

        if token == data["qr_token"]:
            return render_template(
                "edit.html",
                row=data,
                token=token,
                dropdown_art=[
                    s.name
                    for s in Setting.query.filter_by(
                        category="repair_type", is_active=True
                    )
                    .order_by(Setting.sort_order, Setting.name)
                    .all()
                ],
                dropdown_erg=[],
                dropdown_who=[
                    s.name
                    for s in Setting.query.filter_by(
                        category="repairer", is_active=True
                    )
                    .order_by(Setting.sort_order, Setting.name)
                    .all()
                ],
            )
        else:
            return json.dumps({"reply": "error", "error": "invalid token"})
    except Exception as e:
        print(e)
        return json.dumps({"reply": "error", "error": str(e)})


@web_bp.route("/stat-data/<type>", methods=["GET"])
def stat_data(type):
    """
    Get statistics data for charts
    ---
    tags:
      - Web Pages
    operationId: getStatData
    parameters:
      - name: type
        in: path
        required: true
        type: string
        enum: [repairs, devices, time]
    responses:
      200:
        description: Statistics data
    """
    # Fetch all repairs and convert to DataFrame for statistics
    repairs = Repair.query.all()
    repairs_data = [repair.to_dict() for repair in repairs]
    df = pd.DataFrame(repairs_data)

    if df.empty:
        return json.dumps([])

    if type == "repairs":
        # Stacked bar chart grouped by month
        df["datum"] = pd.to_datetime(df["datum"])
        df["month"] = df["datum"].dt.to_period("M")
        df["month"] = df["month"].dt.strftime("%Y-%m")
        df["success"] = (df["status"] == "Repariert").astype(int)
        df["failed"] = (df["status"] == "Nicht Repariert").astype(int)
        df = (
            df.groupby(["month"]).agg({"success": "sum", "failed": "sum"}).reset_index()
        )
        data = df.to_dict(orient="records")
        return json.dumps(data)

    if type == "devices":
        # Pie chart of devices
        df = df.groupby(["reparatur_art"]).size().reset_index(name="count")
        data = []
        for index, row in df.iterrows():
            name = row["reparatur_art"]
            value = row["count"]
            data.append({"name": name, "value": value})
        return json.dumps(data)

    if type == "time":
        # Sunburst chart
        df = (
            df.groupby(["reparatur_art", "status"])
            .agg({"reparatur_dauer": "sum"})
            .reset_index()
        )
        data = []
        for device, group in df.groupby("reparatur_art"):
            device_data = {"name": device, "children": []}
            for status, sub_group in group.groupby("status"):
                if status == "Repariert":
                    status_name = "success"
                elif status == "Nicht Repariert":
                    status_name = "failed"
                else:
                    status_name = "open"
                status_data = {"name": status_name, "children": []}
                for duration, sub_sub_group in sub_group.groupby("reparatur_dauer"):
                    status_data["children"].append(
                        {"name": str(duration), "value": duration}
                    )
                device_data["children"].append(status_data)
            data.append(device_data)
        return json.dumps(data)

    return json.dumps([])


@web_bp.route("/protected")
def protected():
    """Protected test route."""
    return "Logged in as: " + flask_login.current_user.id


@web_bp.route("/export", methods=["GET"])
def export():
    """Export repairs to Excel file."""
    import os

    from flask import send_from_directory

    repairs = Repair.query.all()
    repairs_data = [repair.to_dict() for repair in repairs]
    df = pd.DataFrame(repairs_data)
    filename = "export.xlsx"
    df.to_excel(filename, index=False)
    return send_from_directory(os.getcwd(), filename, as_attachment=True)


@web_bp.route("/createDisclaimer/<id>", methods=["GET"])
def create_disclaimer(id):
    """Generate and download disclaimer PDF."""
    from flask import send_file

    from app.services.pdf_service import PDFService

    try:
        repair = Repair.query.get_or_404(id)
        data = repair.to_dict()
        date = data["datum"]

        pdf_service = PDFService()
        signed_pdf_stream = pdf_service.get_signed_pdf(data["unterschrift"], date)

        if signed_pdf_stream:
            signed_pdf_stream.seek(0)
            print("Successfully created signed PDF.")
            return send_file(
                signed_pdf_stream,
                as_attachment=True,
                download_name=f"Haftungsausschluss_{id}_{date}.pdf",
                mimetype="application/pdf",
            )
        else:
            print("Failed to create signed PDF.")
            return json.dumps({"reply": "error", "error": "Failed to create PDF"})
    except Exception as e:
        print(f"Error in createDisclaimer: {e}")
        return json.dumps({"reply": "error", "error": str(e)})


@web_bp.route("/api/mailexport", methods=["GET"])
def send_mail_export():
    """Send export via email."""
    from app.services.email_service import EmailService
    from app.services.export_service import ExportService

    if not current_app.config["EMAIL_ENABLED"]:
        return json.dumps(
            {"reply": "error", "error": "E-Mail versandt ist deaktiviert."}
        )

    config_mode = "dev" if current_app.config.get("DEBUG") else "prod"
    email_service = EmailService(current_app.config)
    export_service = ExportService()

    if config_mode == "prod":
        repairs = Repair.query.all()
        csv_data = export_service.repairs_to_csv(repairs)
    else:
        # In dev mode, use test data
        with open(current_app.config["IMPORT_EXCEL_PATH"], "rb") as f:
            csv_data = f.read()

    result = email_service.send_export_email(csv_data, filename_prefix="repairs_export")
    return json.dumps(result)
