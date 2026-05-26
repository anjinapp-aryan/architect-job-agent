"""SQLAlchemy ORM models. Portable across SQLite and PostgreSQL."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CompanyORM(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)


class JobORM(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_jobs_fingerprint"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    title: Mapped[str] = mapped_column(String(512))
    company_name: Mapped[str] = mapped_column(String(512), index=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id"), nullable=True
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    salary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_posted: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    search_timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    is_remote: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    scoring_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    gaps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    company = relationship("CompanyORM")
    applications = relationship("ApplicationORM", back_populates="job", cascade="all, delete-orphan")
    resumes = relationship("ResumeORM", back_populates="job", cascade="all, delete-orphan")
    cover_letters = relationship("CoverLetterORM", back_populates="job", cascade="all, delete-orphan")


class ApplicationORM(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="New")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recruiter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    follow_up_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("JobORM", back_populates="applications")


class ResumeORM(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(255))
    source_path: Mapped[str] = mapped_column(Text)
    parsed_text: Mapped[str] = mapped_column(Text)
    is_master: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("JobORM", back_populates="resumes")


class CoverLetterORM(Base):
    __tablename__ = "cover_letters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("JobORM", back_populates="cover_letters")


class SearchRunORM(Base):
    __tablename__ = "search_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    countries: Mapped[list] = mapped_column(JSON, default=list)
    roles: Mapped[list] = mapped_column(JSON, default=list)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_inserted: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)
