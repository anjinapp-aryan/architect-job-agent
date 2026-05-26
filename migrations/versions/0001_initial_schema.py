"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-23

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("name", name="uq_companies_name"),
    )
    op.create_index("ix_companies_name", "companies", ["name"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("company_name", sa.String(length=512), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("salary", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("date_posted", sa.DateTime(), nullable=True),
        sa.Column("search_timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("is_remote", sa.Boolean(), nullable=True),
        sa.Column("match_score", sa.Integer(), nullable=True),
        sa.Column("scoring_breakdown", sa.JSON(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("gaps", sa.JSON(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.UniqueConstraint("fingerprint", name="uq_jobs_fingerprint"),
    )
    op.create_index("ix_jobs_fingerprint", "jobs", ["fingerprint"])
    op.create_index("ix_jobs_company_name", "jobs", ["company_name"])
    op.create_index("ix_jobs_country", "jobs", ["country"])
    op.create_index("ix_jobs_source", "jobs", ["source"])
    op.create_index("ix_jobs_search_timestamp", "jobs", ["search_timestamp"])
    op.create_index("ix_jobs_match_score", "jobs", ["match_score"])

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="New"),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recruiter", sa.String(length=255), nullable=True),
        sa.Column("follow_up_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_applications_job_id", "applications", ["job_id"])
    op.create_index("ix_applications_status", "applications", ["status"])

    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("parsed_text", sa.Text(), nullable=False),
        sa.Column("is_master", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_resumes_is_master", "resumes", ["is_master"])
    op.create_index("ix_resumes_job_id", "resumes", ["job_id"])

    op.create_table(
        "cover_letters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_cover_letters_job_id", "cover_letters", ["job_id"])

    op.create_table(
        "search_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("countries", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("roles", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("sources", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("jobs_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_table("search_runs")
    op.drop_index("ix_cover_letters_job_id", table_name="cover_letters")
    op.drop_table("cover_letters")
    op.drop_index("ix_resumes_job_id", table_name="resumes")
    op.drop_index("ix_resumes_is_master", table_name="resumes")
    op.drop_table("resumes")
    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_index("ix_applications_job_id", table_name="applications")
    op.drop_table("applications")
    for ix in (
        "ix_jobs_match_score",
        "ix_jobs_search_timestamp",
        "ix_jobs_source",
        "ix_jobs_country",
        "ix_jobs_company_name",
        "ix_jobs_fingerprint",
    ):
        op.drop_index(ix, table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_table("companies")
