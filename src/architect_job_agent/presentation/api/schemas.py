"""API DTOs (Pydantic) — kept distinct from domain entities."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ...domain.entities import ApplicationStatus


class JobOut(BaseModel):
    id: int
    title: str
    company_name: str
    location: Optional[str] = None
    country: Optional[str] = None
    source: str
    salary: Optional[str] = None
    url: Optional[str] = None
    date_posted: Optional[datetime] = None
    is_remote: Optional[bool] = None
    match_score: Optional[int] = None
    recommendation: Optional[str] = None


class JobDetailOut(JobOut):
    description: Optional[str] = None
    scoring_breakdown: Optional[dict] = None
    strengths: Optional[list[str]] = None
    gaps: Optional[list[str]] = None


class SearchTriggerIn(BaseModel):
    countries: Optional[list[str]] = None
    roles: Optional[list[str]] = None


class SearchRunOut(BaseModel):
    id: Optional[int]
    started_at: datetime
    finished_at: Optional[datetime] = None
    countries: list[str]
    roles: list[str]
    sources: list[str]
    jobs_found: int
    jobs_inserted: int
    errors: list[str]


class ApplicationIn(BaseModel):
    job_id: int
    status: ApplicationStatus = ApplicationStatus.NEW
    notes: Optional[str] = None
    recruiter: Optional[str] = None


class ApplicationTransitionIn(BaseModel):
    status: ApplicationStatus
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    status: ApplicationStatus
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    recruiter: Optional[str] = None
    follow_up_at: Optional[datetime] = None
    updated_at: datetime


class ScoringOut(BaseModel):
    match_score: int
    scoring_breakdown: dict[str, int]
    strengths: list[str]
    gaps: list[str]
    recommendation: str


class ResumeOut(BaseModel):
    id: int
    label: str
    source_path: str
    is_master: bool
    job_id: Optional[int] = None
    created_at: datetime


class CoverLetterOut(BaseModel):
    id: int
    job_id: int
    content: str
    file_path: Optional[str] = None
    created_at: datetime
