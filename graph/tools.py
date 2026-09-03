"""LangChain tool definitions for the job-hunting graph.

These tools are intentionally simple and deterministic so they can be used in a
LangGraph tool-calling workflow without proxying the full external runtime.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.tools import tool


@tool
def parse_resume_file(resume_path: str) -> dict[str, Any]:
    """Read a resume file and return normalized text for downstream analysis."""
    path = Path(resume_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {resume_path}")

    content = path.read_text(encoding="utf-8", errors="ignore")
    return {"resume_path": str(path), "content_length": len(content), "content_preview": content[:1000]}


@tool
def generate_search_queries(profile_summary: str, target_roles: str = "") -> list[str]:
    """Generate a short list of search queries from the candidate profile summary."""
    base = [part.strip() for part in target_roles.split(",") if part.strip()]
    summary = profile_summary.strip()
    if not summary:
        base = ["software engineer"]
    elif not base:
        base = [summary[:80]]
    return list(dict.fromkeys(base[:6]))


@tool
def save_matched_jobs(jobs_json: str) -> dict[str, Any]:
    """Persist matched job payloads to the local job database model.

    Args:
        jobs_json: JSON string of job metadata array.
    """
    payload = json.loads(jobs_json)
    if not isinstance(payload, list):
        raise ValueError("jobs_json must decode to a list of job objects")
    return {"saved_count": len(payload), "jobs": payload}


TOOL_REGISTRY = [
    parse_resume_file,
    generate_search_queries,
    save_matched_jobs,
]
