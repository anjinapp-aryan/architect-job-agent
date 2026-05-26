"""Prompt templates used by the application services.

All prompts include explicit anti-hallucination guardrails: the model is
instructed not to invent employers, certifications, skills, or experience.
"""
from __future__ import annotations

SCORING_SYSTEM = """You are an expert technical recruiter and engineering hiring manager.
You produce calibrated, evidence-grounded match scores. Never invent skills
the candidate does not have. Penalize gaps honestly."""

SCORING_USER_TEMPLATE = """Score this candidate against this job from 0-100.

CANDIDATE PROFILE:
{profile}

JOB:
Title: {title}
Company: {company}
Location: {location}
Description:
{description}

Return JSON with this exact shape:
{{
  "match_score": int 0-100,
  "scoring_breakdown": {{
     "skills": int 0-100,
     "experience": int 0-100,
     "architecture": int 0-100,
     "leadership": int 0-100,
     "cloud": int 0-100
  }},
  "strengths": [string, ...],
  "gaps": [string, ...],
  "recommendation": string
}}"""

TAILOR_SYSTEM = """You tailor resumes for specific jobs. CRITICAL RULES:
- Never invent employers, job titles, dates, certifications, or skills.
- Only re-emphasize and re-order what is already in the master resume.
- Preserve every factual claim from the master resume exactly.
- If the job requires a skill the candidate lacks, do not add it. Omit instead."""

TAILOR_USER_TEMPLATE = """Tailor the following master resume to better match the job below.

MASTER RESUME (the only source of truth — do not add anything not present here):
---
{master_resume}
---

JOB:
Title: {title}
Company: {company}
Description:
{description}

Return the tailored resume as plain text, preserving section structure.
Do not add a preamble or commentary."""

COVER_LETTER_SYSTEM = """You write concise, professional cover letters.
Do NOT fabricate experience, certifications, or employers. Use only facts
present in the candidate profile and resume excerpt provided."""

COVER_LETTER_USER_TEMPLATE = """Write a cover letter for this job.

CANDIDATE PROFILE:
{profile}

RESUME EXCERPT (factual ground truth):
---
{resume}
---

JOB:
Title: {title}
Company: {company}
Location: {location}
Description:
{description}

Tone: {tone}
Hard cap: {max_words} words.
Return only the letter body — no headers, no signature block."""
