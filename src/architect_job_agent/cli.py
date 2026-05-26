"""Small CLI for local automation: ``python -m architect_job_agent.cli search``."""
from __future__ import annotations

import argparse
import json

from .core.config import get_settings
from .core.logging import configure_logging, get_logger
from .infrastructure.ai.factory import build_ai_provider
from .infrastructure.db.repositories import (
    SQLApplicationRepository,
    SQLJobRepository,
    SQLSearchRunRepository,
)
from .infrastructure.db.session import init_db, session_scope
from .infrastructure.jobspy_client import JobSpyClient
from .application.services import (
    DashboardService,
    JobScoringService,
    JobSearchService,
)


def cmd_search(_: argparse.Namespace) -> None:
    settings = get_settings()
    init_db()
    client = JobSpyClient(
        results_wanted=settings.search.results_per_query,
        rate_limit_seconds=settings.search.rate_limit_seconds,
    )
    with session_scope() as s:
        run = JobSearchService(
            settings, client, SQLJobRepository(s), SQLSearchRunRepository(s)
        ).run_full_search()
        print(json.dumps(run.model_dump(default=str), indent=2))


def cmd_score(args: argparse.Namespace) -> None:
    settings = get_settings()
    init_db()
    ai = build_ai_provider()
    with session_scope() as s:
        repo = SQLJobRepository(s)
        scoring = JobScoringService(settings, ai, repo)
        jobs = repo.list(min_score=None, limit=args.limit)
        for job in jobs:
            if job.match_score is not None and not args.rescore:
                continue
            result = scoring.score_job(job)
            print(f"#{job.id} {job.title} @ {job.company_name} -> {result.match_score}")


def cmd_dashboard(_: argparse.Namespace) -> None:
    settings = get_settings()
    init_db()
    with session_scope() as s:
        out = DashboardService(
            settings,
            SQLJobRepository(s),
            SQLApplicationRepository(s),
            SQLSearchRunRepository(s),
        ).summary()
        print(json.dumps(out, indent=2, default=str))


def main() -> None:
    configure_logging()
    get_logger(__name__)
    parser = argparse.ArgumentParser(prog="architect-job-agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("search", help="Run a full multi-country / multi-role search").set_defaults(func=cmd_search)

    score = sub.add_parser("score", help="AI-score recent jobs")
    score.add_argument("--limit", type=int, default=20)
    score.add_argument("--rescore", action="store_true", help="Rescore already-scored jobs")
    score.set_defaults(func=cmd_score)

    sub.add_parser("dashboard", help="Print dashboard summary").set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
