from io import StringIO

from openpyxl import load_workbook
from rich.console import Console

from tools.excel_export import export_pipeline_results


def test_export_pipeline_results_creates_three_formatted_sheets(tmp_path):
    output_path = tmp_path / "results.xlsx"
    state = {
        "matched_jobs": [
            {
                "title": "AI Engineer",
                "company": "Example Co",
                "source_board": "linkedin",
                "location": "India",
                "source_url": "https://example.com/jobs/123",
                "match_scores": {"composite_score": 0.85},
                "salary_range": "₹15L-₹20L",
                "posted_date": "2026-11-02",
            },
            {
                "title": "=HYPERLINK(\"https://bad.example\")",
                "company": "Formula Test",
                "source_url": "javascript:alert(1)",
                "match_scores": {"composite_score": 0.5},
            },
        ],
        "outreach_summary": {
            "total_attempted": 2,
            "successfully_sent": 0,
            "skipped": 2,
            "failed": 0,
        },
        "tracking_dashboard": {
            "status_breakdown": {"matched": 2},
            "recent_activity": [
                {
                    "company": "Example Co",
                    "title": "AI Engineer",
                    "status": "matched",
                    "last_action": "Job matched",
                    "last_action_at": "2026-11-02",
                    "next_action": "Review application",
                    "next_action_at": "",
                    "job_id": "job-1",
                }
            ],
        },
    }

    saved_path = export_pipeline_results(state, output_path)

    assert saved_path == output_path
    workbook = load_workbook(saved_path, data_only=False)
    assert workbook.sheetnames == ["Matched Jobs", "Outreach Summary", "Application Status"]

    jobs = workbook["Matched Jobs"]
    assert jobs["B2"].value == "AI Engineer"
    assert jobs["I2"].value == "https://example.com/jobs/123"
    assert jobs["I2"].hyperlink.target == "https://example.com/jobs/123"
    assert jobs["F2"].number_format == "0.0%"
    assert jobs["B3"].data_type == "s"
    assert jobs["I3"].hyperlink is None

    outreach = workbook["Outreach Summary"]
    assert outreach["A2"].value == "Total Attempted"
    assert outreach["B2"].value == 2

    dashboard = workbook["Application Status"]
    assert dashboard["A2"].value == "Matched"
    assert dashboard["B2"].value == 2
    assert dashboard["A3"].value == "Total"
    assert dashboard["A5"].value == "Company"
    assert dashboard["A6"].value == "Example Co"


def test_export_pipeline_results_includes_empty_sheets(tmp_path):
    output_path = export_pipeline_results({}, tmp_path / "empty.xlsx")

    workbook = load_workbook(output_path)
    assert workbook.sheetnames == ["Matched Jobs", "Outreach Summary", "Application Status"]
    assert workbook["Matched Jobs"].max_row == 1
    assert workbook["Outreach Summary"]["A2"].value == "Total Attempted"


def test_display_results_exports_after_terminal_results(monkeypatch, tmp_path):
    import main
    from tools import excel_export

    calls = []
    output_path = tmp_path / "job_hunt_results.xlsx"

    def fake_export(state):
        calls.append(state)
        return output_path

    output = StringIO()
    monkeypatch.setattr(main, "console", Console(file=output, width=100, color_system=None))
    monkeypatch.setattr(excel_export, "export_pipeline_results", fake_export)

    state = {
        "matched_jobs": [],
        "outreach_summary": {},
        "tracking_dashboard": {},
    }
    main._display_results(state)

    assert calls == [state]
    rendered = output.getvalue().replace("\n", "").replace("\r", "")
    assert "Excel results saved to:" in rendered
    assert str(output_path) in rendered
