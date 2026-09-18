"""
SQLAlchemy models for RepairCafe application
"""

from datetime import date, datetime
from typing import Optional

import flask_login
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class User(flask_login.UserMixin, db.Model):
    """Reparateur (repair volunteer) user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(100), nullable=False, unique=True)
    vorname: Mapped[Optional[str]] = mapped_column(db.String(100))
    nachname: Mapped[Optional[str]] = mapped_column(db.String(100))
    email: Mapped[str] = mapped_column(db.String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )

    def __repr__(self):
        return f"<User {self.id}: {self.vorname} {self.nachname}>"


class AppConfig(db.Model):
    """Key-value store for application configuration (org name, website, etc.)."""

    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(db.String(100), primary_key=True)
    value: Mapped[str] = mapped_column(db.Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    def __repr__(self):
        return f"<AppConfig {self.key}={self.value!r}>"


class Setting(db.Model):
    """Configuration setting stored in DB (replaces dropdown_data.yaml)."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(db.String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(db.String(100))
    sort_order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    def __repr__(self):
        return f"<Setting {self.id}: [{self.category}] {self.name}>"


class Customer(db.Model):
    """Customer record – reusable contact info across multiple repairs."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    vorname: Mapped[str] = mapped_column(db.String(100), nullable=False)
    nachname: Mapped[str] = mapped_column(db.String(100), nullable=False)
    telefon: Mapped[Optional[str]] = mapped_column(db.String(40))
    email: Mapped[Optional[str]] = mapped_column(db.String(100))
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )

    # Relationship to repairs
    repairs = db.relationship("Repair", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.id}: {self.vorname} {self.nachname}>"


class Repair(db.Model):
    """Repair record model"""

    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("customers.id")
    )
    repair_type_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("settings.id", ondelete="SET NULL"), nullable=True
    )
    datum: Mapped[date] = mapped_column(db.Date, nullable=False, default=datetime.today)
    geraet_art: Mapped[str] = mapped_column(db.String(100), nullable=False)
    defekt_besch: Mapped[Optional[str]] = mapped_column(db.String(400))
    unterschrift_haft: Mapped[Optional[bool]] = mapped_column(db.Boolean)
    unterschrift: Mapped[Optional[str]] = mapped_column(db.Text)
    din_pruef: Mapped[Optional[bool]] = mapped_column(db.Boolean)
    status_detail: Mapped[Optional[str]] = mapped_column(db.String(100))
    reparatur_besch: Mapped[Optional[str]] = mapped_column(db.String(400))
    user_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id")
    )
    reparatur_dauer: Mapped[Optional[int]] = mapped_column(db.SmallInteger)
    status: Mapped[str] = mapped_column(db.String(20), nullable=False, default="Offen")
    closed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    qr_token: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL")
    )

    # Relationship to repair logs
    repair_logs = db.relationship(
        "RepairLog",
        back_populates="repair",
        cascade="all, delete-orphan",
        order_by="RepairLog.created_at",
    )

    # Relationship to VDE tests
    vde_tests = db.relationship(
        "VdeTest",
        back_populates="repair",
        cascade="all, delete-orphan",
        order_by="VdeTest.created_at",
    )

    # Relationship to customer
    customer = db.relationship("Customer", back_populates="repairs")

    # Relationship to repair type setting
    repair_type = db.relationship("Setting", foreign_keys=[repair_type_id])

    # Relationship to assigned user (reparateur)
    user = db.relationship("User", foreign_keys=[user_id])

    # Relationship to user who created the repair record
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    # Relationship to attachments
    attachments = db.relationship(
        "RepairAttachment",
        back_populates="repair",
        cascade="all, delete-orphan",
        order_by="RepairAttachment.uploaded_at",
    )

    def __repr__(self):
        return f"<Repair {self.id}: {self.geraet_art}>"

    def to_dict(self):
        """Convert model to dictionary"""
        d = {
            "id": self.id,
            "customer_id": self.customer_id,
            "repair_type_id": self.repair_type_id,
            "repair_type_name": self.repair_type.name if self.repair_type else None,
            "datum": self.datum.isoformat() if self.datum else None,
            "geraet_art": self.geraet_art,
            "defekt_besch": self.defekt_besch,
            "unterschrift_haft": self.unterschrift_haft,
            "unterschrift": self.unterschrift,
            "din_pruef": self.din_pruef,
            "status_detail": self.status_detail,
            "reparatur_besch": self.reparatur_besch,
            "user_id": self.user_id,
            "reparatur_dauer": self.reparatur_dauer,
            "status": self.status,
            "qr_token": self.qr_token,
        }
        if self.customer:
            d["vorname"] = self.customer.vorname
            d["nachname"] = self.customer.nachname
            d["telefon"] = self.customer.telefon
            d["email"] = self.customer.email
        return d

    @classmethod
    def from_dict(cls, data):
        """Create model from dictionary"""
        return cls(**data)


class RepairLog(db.Model):
    """Repair work log entry model for tracking multiple work sessions on a repair"""

    __tablename__ = "repair_logs"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    repair_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("repairs.id"), nullable=False
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id")
    )
    reparatur_dauer: Mapped[int] = mapped_column(db.SmallInteger, nullable=False)
    reparatur_besch: Mapped[str] = mapped_column(db.String(400), nullable=False)
    log_type: Mapped[str] = mapped_column(db.String(20), nullable=False, default="work")
    status_from: Mapped[Optional[str]] = mapped_column(db.String(20))
    status_to: Mapped[Optional[str]] = mapped_column(db.String(20))
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )

    # Relationship to repair
    repair = db.relationship("Repair", back_populates="repair_logs")
    # Relationship to assigned user (reparateur)
    user = db.relationship("User", foreign_keys=[user_id])

    # Relationship to attachments linked to this log entry
    attachments = db.relationship(
        "RepairAttachment",
        back_populates="log",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<RepairLog {self.id}: Repair {self.repair_id} by user {self.user_id}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "repair_id": self.repair_id,
            "user_id": self.user_id,
            "reparatur_dauer": self.reparatur_dauer,
            "reparatur_besch": self.reparatur_besch,
            "log_type": self.log_type,
            "status_from": self.status_from,
            "status_to": self.status_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data):
        """Create model from dictionary"""
        return cls(**data)


class VdeTest(db.Model):
    """VDE electrical safety test results model"""

    __tablename__ = "vde_tests"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    repair_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("repairs.id"), nullable=False
    )

    # General information
    prufer: Mapped[Optional[str]] = mapped_column(
        db.String(100)
    )  # Legacy text; derived from prufer_user
    prufer_user_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id")
    )
    electrician: Mapped[Optional[str]] = mapped_column(
        db.String(100)
    )  # Electrician supervising EuP test
    pruefgeraet_name: Mapped[Optional[str]] = mapped_column(
        db.String(100)
    )  # Testing device name
    pruefgeraet_serial: Mapped[Optional[str]] = mapped_column(
        db.String(100)
    )  # Testing device serial number

    # Visual inspection — True = i.O. (passed), False = n.i.O. (failed), None = not checked
    sichtpruefung_gehaeuse: Mapped[Optional[bool]] = mapped_column(db.Boolean)
    sichtpruefung_kabel: Mapped[Optional[bool]] = mapped_column(db.Boolean)
    sichtpruefung_stecker: Mapped[Optional[bool]] = mapped_column(db.Boolean)
    sichtpruefung_zugentlastung: Mapped[Optional[bool]] = mapped_column(db.Boolean)
    sichtpruefung_sicherheit: Mapped[Optional[bool]] = mapped_column(db.Boolean)

    # Electrical tests — True = bestanden, False = nicht bestanden, None = not tested
    schutzklasse: Mapped[Optional[str]] = mapped_column(db.String(50))
    schutzleiter_pruefung: Mapped[Optional[bool]] = mapped_column(db.Boolean)
    isolationspruefung: Mapped[Optional[bool]] = mapped_column(db.Boolean)
    ableitstrom_pruefung: Mapped[Optional[bool]] = mapped_column(db.Boolean)

    # Overall result — True = bestanden, False = nicht bestanden
    gesamtergebnis: Mapped[bool] = mapped_column(db.Boolean, nullable=False)
    bemerkungen: Mapped[Optional[str]] = mapped_column(db.Text)

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )

    # Relationships
    repair = db.relationship("Repair", back_populates="vde_tests")
    prufer_user = db.relationship("User", foreign_keys=[prufer_user_id])

    def __repr__(self):
        return f"<VdeTest {self.id}: Repair {self.repair_id} - {self.gesamtergebnis}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "repair_id": self.repair_id,
            "prufer": self.prufer,
            "electrician": self.electrician,
            "pruefgeraet_name": self.pruefgeraet_name,
            "pruefgeraet_serial": self.pruefgeraet_serial,
            "sichtpruefung_gehaeuse": self.sichtpruefung_gehaeuse,
            "sichtpruefung_kabel": self.sichtpruefung_kabel,
            "sichtpruefung_stecker": self.sichtpruefung_stecker,
            "sichtpruefung_zugentlastung": self.sichtpruefung_zugentlastung,
            "sichtpruefung_sicherheit": self.sichtpruefung_sicherheit,
            "schutzklasse": self.schutzklasse,
            "schutzleiter_pruefung": self.schutzleiter_pruefung,
            "isolationspruefung": self.isolationspruefung,
            "ableitstrom_pruefung": self.ableitstrom_pruefung,
            "gesamtergebnis": self.gesamtergebnis,
            "bemerkungen": self.bemerkungen,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data):
        """Create model from dictionary"""
        return cls(**data)


ATTACHMENT_TYPES = ("log_entry", "device_photo", "disclaimer", "misc")


class RepairAttachment(db.Model):
    """Unified file attachment store for all repair-related files."""

    __tablename__ = "repair_attachments"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    repair_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False
    )
    log_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("repair_logs.id", ondelete="SET NULL"), nullable=True
    )
    attachment_type: Mapped[str] = mapped_column(
        db.String(50), nullable=False, default="misc"
    )
    original_filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(
        db.String(255), nullable=False, unique=True
    )
    content_type: Mapped[str] = mapped_column(db.String(100), nullable=False)
    size: Mapped[int] = mapped_column(db.Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    repair = db.relationship("Repair", back_populates="attachments")
    log = db.relationship("RepairLog", back_populates="attachments")
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_id])

    def __repr__(self):
        return (
            f"<RepairAttachment {self.id}: repair={self.repair_id}"
            f" type={self.attachment_type} file={self.original_filename}>"
        )
