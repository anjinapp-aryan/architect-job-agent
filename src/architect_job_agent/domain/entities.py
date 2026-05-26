"""Pure domain entities — framework-agnostic Pydantic models.

These represent the conceptual shape of business objects and are independent
of the persistence layer (SQLAlchemy models) and the API DTOs.
"""
from __future__ import annotations

import enum
import hashlib
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ApplicationStatus(str, enum.Enum):
    NEW = "New"
    SAVED = "Saved"
    APPLIED = "Applied"
    INTERVIEW = "Interview"
    REJECTED = "Rejected"
    OFFER = "Offer"
    ACCEPTED = "Accepted"


class JobSource(str, enum.Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    ZIPRECRUITER = "zip_recruiter"
    OTHER = "other"


class Company(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None


class Job(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    fingerprint: str
    title: str
    company_name: str
    location: Optional[str] = None
    country: Optional[str] = None
    source: str
    salary: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    date_posted: Optional[datetime] = None
    search_timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_remote: Optional[bool] = None
    match_score: Optional[int] = None
    scoring_breakdown: Optional[dict[str, Any]] = None
    strengths: Optional[list[str]] = None
    gaps: Optional[list[str]] = None
    recommendation: Optional[str] = None

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not (v.startswith("http://") or v.startswith("https://")):
            return None
        return v

    @staticmethod
    def make_fingerprint(
        title: str, company: str, location: str | None, url: str | None
    ) -> str:
        raw = "|".join(
            [
                (title or "").strip().lower(),
                (company or "").strip().lower(),
                (location or "").strip().lower(),
                (url or "").strip().lower(),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SearchRun(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    countries: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    jobs_found: int = 0
    jobs_inserted: int = 0
    errors: list[str] = Field(default_factory=list)


class Application(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    job_id: int
    status: ApplicationStatus = ApplicationStatus.NEW
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    recruiter: Optional[str] = None
    follow_up_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Resume(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    label: str
    source_path: str
    parsed_text: str
    is_master: bool = False
    job_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CoverLetter(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    job_id: int
    content: str
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScoringResult(BaseModel):
    match_score: int = Field(ge=0, le=100)
    scoring_breakdown: dict[str, int] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    recommendation: str = ""
