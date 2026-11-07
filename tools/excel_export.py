"""Export a completed job-search run to a formatted Excel workbook."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


_HEADER_FILL = PatternFill(fill_type="solid", fgColor="1F4E78")
_HEADER_FONT = Font(color="FFFFFF", bold=True)
_HYPERLINK_FONT = Font(color="0563C1", underline="single")


def export_pipeline_results(
    state: dict[str, Any],
    output_path: str | Path | None = None,
) -> Path:
    """Write matched jobs, outreach summary, and application status to one workbook."""
    destination = Path(output_path) if output_path else (
        Path(__file__).resolve().parent.parent / "data" / "job_hunt_results.xlsx"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    jobs_sheet = workbook.active
    jobs_sheet.title = "Matched Jobs"
    _write_matched_jobs(jobs_sheet, state.get("matched_jobs") or [])

    outreach_sheet = workbook.create_sheet("Outreach Summary")
    _write_key_value_sheet(
        outreach_sheet,
        ("Metric", "Value"),
        state.get("outreach_summary") or {
            "total_attempted": 0,
            "successfully_sent": 0,
            "skipped": 0,
            "failed": 0,
        },
    )

    dashboard_sheet = workbook.create_sheet("Application Status")
    _write_dashboard(dashboard_sheet, state.get("tracking_dashboard") or {})

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".xlsx",
            prefix=f".{destination.stem}-",
            dir=destination.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
        workbook.save(temp_path)
        os.replace(temp_path, destination)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()

    return destination


def _write_matched_jobs(worksheet, jobs: list[dict[str, Any]]) -> None:
    headers = [
        "#",
        "Title",
        "Company",
        "Source",
        "Location",
        "Match Score",
        "Salary",
        "Posted Date",
        "Apply Link",
    ]
    worksheet.append(headers)

    for index, job in enumerate(jobs, start=1):
        scores = job.get("match_scores") or {}
        row = [
            index,
            job.get("title", ""),
            job.get("company", ""),
            job.get("source_board", ""),
            job.get("location", ""),
            scores.get("composite_score", 0),
            job.get("salary_range") or "",
            job.get("posted_date") or "",
            job.get("source_url") or "",
        ]
        worksheet.append([_safe_cell_value(value) for value in row])

        link_cell = worksheet.cell(row=worksheet.max_row, column=9)
        if _is_http_url(link_cell.value):
            link_cell.hyperlink = link_cell.value
            link_cell.font = _HYPERLINK_FONT
        if isinstance(scores.get("composite_score"), (int, float)):
            worksheet.cell(row=worksheet.max_row, column=6).number_format = "0.0%"

    _format_table(worksheet, len(headers))
    worksheet.auto_filter.ref = worksheet.dimensions


def _write_key_value_sheet(worksheet, headers: tuple[str, str], values: dict[str, Any]) -> None:
    worksheet.append(headers)
    for key, value in values.items():
        worksheet.append([_safe_cell_value(key.replace("_", " ").title()), _safe_cell_value(value)])
    _format_table(worksheet, 2)


def _write_dashboard(worksheet, dashboard: dict[str, Any]) -> None:
    worksheet.append(["Status", "Count"])
    breakdown = dashboard.get("status_breakdown") or {}
    for status, count in breakdown.items():
        worksheet.append([
            _safe_cell_value(str(status).replace("_", " ").title()),
            _safe_cell_value(count),
        ])
    worksheet.append(["Total", sum(breakdown.values())])
    _format_header(worksheet, 2, row=1)

    activity_start = worksheet.max_row + 2
    activity_headers = [
        "Company",
        "Title",
        "Status",
        "Last Action",
        "Last Action At",
        "Next Action",
        "Next Action At",
        "Job ID",
    ]
    for column, header in enumerate(activity_headers, start=1):
        worksheet.cell(row=activity_start, column=column, value=header)

    for row_index, activity in enumerate(dashboard.get("recent_activity") or [], start=activity_start + 1):
        for column, key in enumerate(
            ("company", "title", "status", "last_action", "last_action_at",
             "next_action", "next_action_at", "job_id"),
            start=1,
        ):
            worksheet.cell(
                row=row_index,
                column=column,
                value=_safe_cell_value(activity.get(key, "")),
            )

    _format_header(worksheet, len(activity_headers), row=activity_start)
    worksheet.freeze_panes = "A2"
    _set_column_widths(worksheet)


def _format_table(worksheet, column_count: int) -> None:
    _format_header(worksheet, column_count)
    worksheet.freeze_panes = "A2"
    _set_column_widths(worksheet)


def _format_header(worksheet, column_count: int, row: int = 1) -> None:
    for cell in worksheet[row][:column_count]:
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)


def _set_column_widths(worksheet) -> None:
    for column_cells in worksheet.columns:
        max_length = max(
            (len(str(cell.value)) for cell in column_cells if cell.value is not None),
            default=0,
        )
        worksheet.column_dimensions[get_column_letter(column_cells[0].column)].width = min(
            max(max_length + 2, 12),
            60,
        )
    for row in worksheet.iter_rows():
        for cell in row:
            if cell.row != 1 and cell.value is not None:
                cell.alignment = Alignment(vertical="top", wrap_text=True)


def _safe_cell_value(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("="):
        return "'" + value
    return value


def _is_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
