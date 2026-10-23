from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from api.models import Role

# Emails are compared case-insensitively, so they're lowercased before anything else sees them.
Email = Annotated[EmailStr, AfterValidator(str.lower)]


class SignupIn(BaseModel):
    """No `role` field: everyone who signs up is a regular user."""

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    email: Email
    password: Annotated[str, Field(min_length=8, max_length=128)]


class LoginIn(BaseModel):
    email: Email
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: Role
    created_at: datetime
    updated_at: datetime
