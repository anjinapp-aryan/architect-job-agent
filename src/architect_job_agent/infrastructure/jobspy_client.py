"""Thin adapter around the ``python-jobspy`` package.

Maps our internal source identifiers to JobSpy site keys, applies retry +
rate-limit handling, and converts results into domain :class:`Job` objects.
The actual `jobspy` import is local so the rest of the app stays importable
in environments where the package isn't installed (CI, frontend-only).
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Iterable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..core.exceptions import JobSourceUnavailableError, RateLimitedError
from ..core.logging import get_logger
from ..domain.entities import Job

logger = get_logger(__name__)

_SOURCE_MAP = {
    "linkedin": "linkedin",
    "indeed": "indeed",
    "glassdoor": "glassdoor",
    "zip_recruiter": "zip_recruiter",
    "ziprecruiter": "zip_recruiter",
}


class JobSpyClient:
    def __init__(self, results_wanted: int = 25, rate_limit_seconds: int = 5) -> None:
        self.results_wanted = results_wanted
        self.rate_limit_seconds = rate_limit_seconds

    @retry(
        retry=retry_if_exception_type((JobSourceUnavailableError, RateLimitedError)),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _scrape(self, **kwargs):
        try:
            from jobspy import scrape_jobs  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise JobSourceUnavailableError("python-jobspy not installed") from exc
        try:
            return scrape_jobs(**kwargs)
        except Exception as exc:
            msg = str(exc).lower()
            if "429" in msg or "rate" in msg:
                raise RateLimitedError(str(exc)) from exc
            raise JobSourceUnavailableError(str(exc)) from exc

    def search(
        self,
        role: str,
        country: str,
        sources: Iterable[str],
        max_age_days: int = 30,
        remote_allowed: bool = True,
    ) -> list[Job]:
        site_names = [_SOURCE_MAP[s] for s in sources if s in _SOURCE_MAP]
        if not site_names:
            return []

        logger.info("jobspy.search.start", role=role, country=country, sources=site_names)
        try:
            df = self._scrape(
                site_name=site_names,
                search_term=role,
                location=country,
                results_wanted=self.results_wanted,
                hours_old=max_age_days * 24,
                country_indeed=country,
                is_remote=None if remote_allowed else False,
            )
        except (JobSourceUnavailableError, RateLimitedError) as exc:
            logger.error("jobspy.search.failed", role=role, country=country, error=str(exc))
            return []
        finally:
            time.sleep(self.rate_limit_seconds)

        if df is None or len(df) == 0:
            logger.info("jobspy.search.empty", role=role, country=country)
            return []

        out: list[Job] = []
        for _, row in df.iterrows():
            title = str(row.get("title") or "").strip()
            company = str(row.get("company") or "").strip() or "Unknown Company"
            if not title:
                continue
            location = self._coerce(row.get("location"))
            url = self._coerce(row.get("job_url"))
            source = str(row.get("site") or "").strip().lower() or "other"
            fingerprint = Job.make_fingerprint(title, company, location, url)
            try:
                date_posted = self._parse_date(row.get("date_posted"))
            except Exception:
                date_posted = None
            salary = self._format_salary(row)
            out.append(
                Job(
                    fingerprint=fingerprint,
                    title=title,
                    company_name=company,
                    location=location,
                    country=country,
                    source=source,
                    salary=salary,
                    url=url,
                    description=self._coerce(row.get("description")),
                    date_posted=date_posted,
                    is_remote=bool(row.get("is_remote")) if row.get("is_remote") is not None else None,
                )
            )
        logger.info("jobspy.search.done", role=role, country=country, count=len(out))
        return out

    @staticmethod
    def _coerce(value) -> str | None:
        if value is None:
            return None
        s = str(value).strip()
        return s or None

    @staticmethod
    def _parse_date(value) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

    @staticmethod
    def _format_salary(row) -> str | None:
        min_s = row.get("min_amount")
        max_s = row.get("max_amount")
        currency = row.get("currency") or ""
        interval = row.get("interval") or ""
        parts = []
        if min_s:
            parts.append(str(min_s))
        if max_s:
            parts.append(str(max_s))
        if not parts:
            return None
        return f"{currency} {'-'.join(parts)} {interval}".strip()
