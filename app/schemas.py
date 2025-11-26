import uuid
from datetime import datetime, time
from typing import Any, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class RoleBase(BaseModel):
    name: str
    description: str | None = None
    permissions: dict[str, list[str]] = Field(default_factory=dict)


class RoleCreate(RoleBase):
    pass


class RoleOut(RoleBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentBase(BaseModel):
    name: str
    description: str | None = None
    manager_id: uuid.UUID | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentOut(DepartmentBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ShiftBase(BaseModel):
    name: str
    start_time: time
    end_time: time
    grace_period_minutes: int = 0
    working_days: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])


class ShiftCreate(ShiftBase):
    pass


class ShiftOut(ShiftBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    employee_id: str
    role_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    shift_id: uuid.UUID | None = None
    is_active: bool = True
    notification_preferences: dict[str, bool] = Field(
        default_factory=lambda: {"registration": True, "reset": True, "attendance": True}
    )


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    shift_id: uuid.UUID | None = None
    is_active: bool | None = None
    notification_preferences: dict[str, bool] | None = None


class UserOut(UserBase):
    id: uuid.UUID
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AuthTokens(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserOut
    tokens: AuthTokens


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegistrationRequest(UserCreate):
    pass


class EmailVerificationRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class QRCodeOut(BaseModel):
    code_data: str
    expires_at: datetime | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class AttendanceCreate(BaseModel):
    code_data: str
    location: str | None = None
    notes: str | None = None
    action: Literal["check_in", "check_out"] = "check_in"


class AttendanceOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    check_in: datetime
    check_out: datetime | None
    status: str
    location: str | None
    notes: str | None
    shift_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AttendanceSummary(BaseModel):
    total_check_ins: int
    late_count: int
    range_start: datetime
    range_end: datetime


class ReportExport(BaseModel):
    format: Literal["csv", "pdf"] = "csv"
    range_start: datetime
    range_end: datetime
    department_id: uuid.UUID | None = None


class BiometricEnrollment(BaseModel):
    user_id: uuid.UUID
    biometric_type: str
    biometric_hash: str


class AuditLogOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    resource: str
    changes: Optional[dict[str, Any]]
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
