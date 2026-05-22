"""
Pydantic schemas for request validation and response serialization
"""

from datetime import date, datetime
from typing import Annotated, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)
from pydantic.functional_serializers import PlainSerializer

# Datetime type that always serializes as UTC ISO-8601 with 'Z' suffix.
# Use for all created_at / updated_at fields in response schemas so the
# browser correctly interprets the value as UTC instead of local time.
UtcDatetime = Annotated[
    datetime,
    PlainSerializer(
        lambda v: v.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
        return_type=str,
        when_used="json",
    ),
]

VALID_REPAIR_STATUSES = {
    "Offen",
    "In Bearbeitung",
    "Repariert",
    "Nicht Repariert",
}

VALID_STATUS_DETAILS = {
    "Offen": set(),
    "In Bearbeitung": {"Ersatzteilbesorgung"},
    "Repariert": set(),
    "Nicht Repariert": {"Nicht moeglich", "Abbruch", "Wartezeit zu lang"},
}


# ---------------------------------------------------------------------------
# Shared validator helpers (used by multiple schema classes)
# ---------------------------------------------------------------------------


def _parse_date_value(value, allow_none: bool = False):
    """Parse a date from string, date, or datetime.  Used as a field validator."""
    if value is None:
        return None if allow_none else value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            pass
        for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"]:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unable to parse date: {value}")
    return value


def _empty_string_to_none(value):
    """Convert empty / blank strings to None for optional fields."""
    if value == "" or (isinstance(value, str) and not value.strip()):
        return None
    return value


# ---------------------------------------------------------------------------
# User (Reparateur) schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=1, max_length=100)
    vorname: str = Field(..., min_length=1, max_length=100)
    nachname: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8)
    is_admin: bool = False
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating an existing user (all fields optional)."""

    username: Optional[str] = Field(None, min_length=1, max_length=100)
    vorname: Optional[str] = Field(None, min_length=1, max_length=100)
    nachname: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Schema for user responses — never includes the password hash."""

    id: int
    username: str
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    email: str
    is_admin: bool
    is_active: bool
    created_at: UtcDatetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Schema for login credentials."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Customer schemas
# ---------------------------------------------------------------------------


class CustomerCreate(BaseModel):
    """Schema for creating a new customer"""

    vorname: str = Field(..., min_length=1, max_length=100)
    nachname: str = Field(..., min_length=1, max_length=100)
    telefon: Optional[str] = Field(None, max_length=40)
    email: Optional[EmailStr] = Field(None, max_length=100)

    model_config = ConfigDict(from_attributes=True)


class CustomerResponse(BaseModel):
    """Schema for customer responses"""

    id: int
    vorname: str
    nachname: str
    telefon: Optional[str] = None
    email: Optional[str] = None
    created_at: UtcDatetime

    model_config = ConfigDict(from_attributes=True)


class CustomerWithRepairCountResponse(CustomerResponse):
    """Customer response extended with repair count — used by the customer list endpoint."""

    repair_count: int = Field(0, description="Number of repairs for this customer")


class RepairBase(BaseModel):
    """Base repair schema with common fields"""

    datum: date = Field(..., description="Date of repair intake")
    reparatur_art: str = Field(
        ..., min_length=1, max_length=100, description="Repair category"
    )
    reparatur_sonstiges: Optional[str] = Field(
        None, max_length=100, description="Other repair category"
    )
    geraet_art: str = Field(
        ..., min_length=1, max_length=100, description="Device type"
    )
    defekt_besch: Optional[str] = Field(
        None, max_length=400, description="Defect description"
    )
    unterschrift: Optional[str] = Field(None, description="Signature image as base64")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("datum", mode="before")
    @classmethod
    def parse_date(cls, value):
        return _parse_date_value(value)


class RepairCreate(RepairBase):
    """Schema for creating a new repair"""

    vorname: str = Field(..., min_length=1, max_length=100, description="First name")
    nachname: str = Field(..., min_length=1, max_length=100, description="Last name")
    telefon: Optional[str] = Field(None, max_length=40, description="Phone number")
    email: Optional[EmailStr] = Field(None, max_length=100, description="Email address")
    customer_id: Optional[int] = Field(None, description="Link to existing customer")

    @field_validator("email", mode="before")
    @classmethod
    def empty_string_to_none(cls, value):
        return _empty_string_to_none(value)


class RepairUpdate(BaseModel):
    """Schema for updating an existing repair"""

    datum: Optional[date] = Field(None, description="Date of repair intake")
    reparatur_art: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Repair category"
    )
    reparatur_sonstiges: Optional[str] = Field(
        None, max_length=100, description="Other repair category"
    )
    geraet_art: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Device type"
    )
    defekt_besch: Optional[str] = Field(
        None, max_length=400, description="Defect description"
    )
    unterschrift_haft: Optional[bool] = Field(
        None, description="Liability disclaimer signed"
    )
    unterschrift: Optional[str] = Field(None, description="Signature image as base64")
    din_pruef: Optional[bool] = Field(None, description="DIN test performed")
    status_detail: Optional[str] = Field(
        None, max_length=100, description="Additional detail for repair status"
    )
    reparatur_besch: Optional[str] = Field(
        None, max_length=400, description="Repair description"
    )
    user_id: Optional[int] = Field(None, description="Assigned reparateur (user FK)")
    reparatur_dauer: Optional[int] = Field(
        None, ge=0, description="Repair duration in minutes"
    )
    status: Optional[str] = Field(
        None,
        pattern="^(Offen|In Bearbeitung|Repariert|Nicht Repariert)$",
        description="Repair status",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("datum", mode="before")
    @classmethod
    def parse_date(cls, value):
        return _parse_date_value(value, allow_none=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        """Validate status against canonical set."""
        if value is None:
            return value
        if value not in VALID_REPAIR_STATUSES:
            raise ValueError(f"Invalid status: {value}")
        return value

    @field_validator("status_detail")
    @classmethod
    def normalize_status_detail(cls, value):
        """Normalize empty status_detail values to None."""
        if value == "" or (isinstance(value, str) and not value.strip()):
            return None
        return value

    @model_validator(mode="after")
    def validate_status_detail_rules(self):
        """Ensure status_detail follows the status-specific rules."""
        if self.status is None:
            if self.status_detail is not None:
                raise ValueError("status must be provided when status_detail is set")
            return self

        allowed_details = VALID_STATUS_DETAILS[self.status]

        if self.status == "Nicht Repariert" and self.status_detail is None:
            raise ValueError(
                "status_detail is required when status is 'Nicht Repariert'"
            )

        if self.status_detail is not None and self.status_detail not in allowed_details:
            raise ValueError(
                f"Invalid status_detail '{self.status_detail}' for status '{self.status}'"
            )

        return self


class RepairResponse(RepairBase):
    """Schema for repair response"""

    id: int = Field(..., description="Repair ID")
    customer_id: Optional[int] = Field(None, description="Linked customer ID")
    customer: Optional["CustomerResponse"] = Field(
        None, description="Linked customer object"
    )
    unterschrift_haft: Optional[bool] = Field(
        None, description="Liability disclaimer signed"
    )
    din_pruef: Optional[bool] = Field(None, description="DIN test performed")
    status_detail: Optional[str] = Field(
        None, max_length=100, description="Additional detail for repair status"
    )
    reparatur_besch: Optional[str] = Field(
        None, max_length=400, description="Repair description"
    )
    user_id: Optional[int] = Field(None, description="Assigned reparateur (user FK)")
    user: Optional["UserResponse"] = Field(
        None, description="Assigned reparateur user object"
    )
    reparatur_dauer: Optional[int] = Field(
        None, ge=0, description="Repair duration in minutes"
    )
    status: str = Field(
        default="Offen",
        pattern="^(Offen|In Bearbeitung|Repariert|Nicht Repariert)$",
        description="Repair status",
    )
    qr_token: str = Field(..., max_length=32, description="QR code token")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("datum", mode="before")
    @classmethod
    def parse_date(cls, value):
        return _parse_date_value(value)


class RepairListResponse(BaseModel):
    """Schema for listing repairs"""

    data: list[RepairResponse]
    total: int = Field(..., description="Total number of repairs")

    model_config = ConfigDict(from_attributes=True)


class APIResponse(BaseModel):
    """Generic API response"""

    reply: str = Field(..., description="Response status (done, error)")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if reply is error")

    model_config = ConfigDict(from_attributes=True)


class RepairCreateResponse(APIResponse):
    """Response for repair creation"""

    id: Optional[int] = Field(None, description="Created repair ID")
    data: Optional[RepairResponse] = Field(None, description="Created repair data")

    model_config = ConfigDict(from_attributes=True)


class RepairLogBase(BaseModel):
    """Base repair log schema with common fields"""

    user_id: Optional[int] = Field(None, description="Assigned reparateur (user FK)")
    reparatur_dauer: int = Field(0, ge=0, description="Repair duration in minutes")
    reparatur_besch: str = Field("", max_length=400, description="Repair description")
    log_type: str = Field(
        "work",
        max_length=20,
        description="Entry type: 'work' for work sessions, 'status_change' for status transitions",
    )
    status_from: Optional[str] = Field(
        None, max_length=20, description="Status before the transition"
    )
    status_to: Optional[str] = Field(
        None, max_length=20, description="Status after the transition"
    )

    model_config = ConfigDict(from_attributes=True)


class RepairLogCreate(RepairLogBase):
    """Schema for creating a new repair log entry"""

    repair_id: int = Field(..., description="Repair ID this log belongs to")


class RepairLogUpdate(BaseModel):
    """Schema for updating an existing repair log entry"""

    user_id: Optional[int] = Field(None, description="Assigned reparateur (user FK)")
    reparatur_dauer: Optional[int] = Field(None, ge=0)
    reparatur_besch: Optional[str] = Field(None, min_length=1, max_length=400)

    model_config = ConfigDict(from_attributes=True)


class RepairLogResponse(RepairLogBase):
    """Schema for repair log response"""

    id: int = Field(..., description="Repair log ID")
    repair_id: int = Field(..., description="Repair ID this log belongs to")
    created_at: UtcDatetime = Field(..., description="When this log entry was created")
    user: Optional["UserResponse"] = Field(
        None, description="Assigned reparateur user object"
    )

    model_config = ConfigDict(from_attributes=True)


class RepairLogListResponse(BaseModel):
    """Schema for listing repair logs"""

    data: list[RepairLogResponse]
    total: int = Field(..., description="Total number of repair logs")

    model_config = ConfigDict(from_attributes=True)


class VdeTestBase(BaseModel):
    """Base VDE test schema with common fields"""

    prufer: Optional[str] = Field(
        None,
        max_length=100,
        description="Tester name (legacy text, derived from prufer_user_id)",
    )
    prufer_user_id: Optional[int] = Field(
        None, description="FK to users table — who performed the test"
    )
    electrician: Optional[str] = Field(
        None, max_length=100, description="Electrician supervising EuP test"
    )
    pruefgeraet_name: Optional[str] = Field(
        None, max_length=100, description="Testing device name"
    )
    pruefgeraet_serial: Optional[str] = Field(
        None, max_length=100, description="Testing device serial number"
    )

    # Visual inspection — True = i.O. (passed), False = n.i.O. (failed), None = not checked
    sichtpruefung_gehaeuse: Optional[bool] = Field(
        None, description="Housing inspection: True=passed, False=failed"
    )
    sichtpruefung_kabel: Optional[bool] = Field(
        None, description="Cable inspection: True=passed, False=failed"
    )
    sichtpruefung_stecker: Optional[bool] = Field(
        None, description="Plug inspection: True=passed, False=failed"
    )
    sichtpruefung_zugentlastung: Optional[bool] = Field(
        None, description="Strain relief inspection: True=passed, False=failed"
    )
    sichtpruefung_sicherheit: Optional[bool] = Field(
        None, description="Safety devices inspection: True=passed, False=failed"
    )

    # Electrical tests — True = bestanden, False = nicht bestanden, None = not tested
    schutzklasse: Optional[str] = Field(None, description="Protection class")
    schutzleiter_pruefung: Optional[bool] = Field(
        None, description="Protective conductor test: True=passed, False=failed"
    )
    isolationspruefung: Optional[bool] = Field(
        None, description="Insulation test: True=passed, False=failed"
    )
    ableitstrom_pruefung: Optional[bool] = Field(
        None, description="Leakage current test: True=passed, False=failed"
    )

    # Overall result
    gesamtergebnis: bool = Field(
        ..., description="Overall result: True=passed, False=failed"
    )
    bemerkungen: Optional[str] = Field(None, description="Comments/Defects")

    model_config = ConfigDict(from_attributes=True)


class VdeTestCreate(VdeTestBase):
    """Schema for creating a new VDE test"""

    repair_id: int = Field(..., description="Repair ID this test belongs to")
    created_at: Optional[datetime] = Field(
        None, description="When this test was performed (defaults to now)"
    )


class VdeTestResponse(VdeTestBase):
    """Schema for VDE test response"""

    id: int = Field(..., description="VDE test ID")
    repair_id: int = Field(..., description="Repair ID this test belongs to")
    created_at: UtcDatetime = Field(..., description="When this test was performed")

    model_config = ConfigDict(from_attributes=True)


class VdeTestListResponse(BaseModel):
    """Schema for listing VDE tests"""

    data: list[VdeTestResponse]
    total: int = Field(..., description="Total number of VDE tests")

    model_config = ConfigDict(from_attributes=True)


class VdeTestCreateResponse(APIResponse):
    """Response for VDE test creation"""

    id: Optional[int] = Field(None, description="Created VDE test ID")
    data: Optional[VdeTestResponse] = Field(None, description="Created VDE test data")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Settings schemas (DB-backed configuration, replaces dropdown_data.yaml)
# ---------------------------------------------------------------------------


class PruefgeraetResponse(BaseModel):
    """Schema for a testing device (Prüfgerät) from the DB settings table."""

    id: int = Field(..., description="Setting ID")
    name: str = Field(..., description="Device name")
    serial_number: Optional[str] = Field(None, description="Device serial number")

    model_config = ConfigDict(from_attributes=True)


class SettingCreate(BaseModel):
    """Schema for creating a new setting entry."""

    category: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    serial_number: Optional[str] = Field(None, max_length=100)
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class SettingUpdate(BaseModel):
    """Schema for updating an existing setting entry."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    serial_number: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class SettingResponse(BaseModel):
    """Schema for setting responses."""

    id: int
    category: str
    name: str
    serial_number: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
