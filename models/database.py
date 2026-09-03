"""
SQLite database setup with table creation and CRUD helper functions.
"""
import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from models.schemas import MatchedJob, OutreachResult, ReplyClassification


class Database:
    """Lightweight SQLite database manager."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _create_tables(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    source_board TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    salary_range TEXT,
                    description TEXT NOT NULL,
                    posted_date TEXT,
                    scraped_at TEXT NOT NULL,
                    composite_match_score REAL NOT NULL,
                    semantic_score REAL,
                    tfidf_score REAL,
                    skill_overlap_score REAL,
                    llm_score REAL,
                    skill_analysis_json TEXT,
                    status TEXT DEFAULT 'matched'
                );

                CREATE TABLE IF NOT EXISTS outreach (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL REFERENCES jobs(id),
                    contact_name TEXT,
                    contact_email TEXT,
                    contact_title TEXT,
                    contact_source TEXT,
                    email_subject TEXT NOT NULL,
                    email_body TEXT NOT NULL,
                    message_id TEXT,
                    sent_at TEXT NOT NULL,
                    email_type TEXT DEFAULT 'initial',
                    status TEXT DEFAULT 'sent'
                );

                CREATE TABLE IF NOT EXISTS replies (
                    id TEXT PRIMARY KEY,
                    outreach_id TEXT NOT NULL REFERENCES outreach(id),
                    from_email TEXT NOT NULL,
                    subject TEXT,
                    body_snippet TEXT,
                    classification TEXT NOT NULL,
                    confidence REAL,
                    received_at TEXT NOT NULL,
                    processed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS follow_up_queue (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL REFERENCES jobs(id),
                    scheduled_at TEXT NOT NULL,
                    follow_up_number INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    sent_at TEXT
                );
            """)

    # ── Jobs ──

    def insert_job(self, job: MatchedJob):
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO jobs
                   (id, source_board, source_url, title, company, location,
                    salary_range, description, posted_date, scraped_at,
                    composite_match_score, semantic_score, tfidf_score,
                    skill_overlap_score, llm_score, skill_analysis_json, status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    job.job_id, job.source_board, job.source_url,
                    job.title, job.company, job.location,
                    job.salary_range, job.description, job.posted_date,
                    datetime.utcnow().isoformat(),
                    job.match_scores.composite_score,
                    job.match_scores.semantic_similarity,
                    job.match_scores.tfidf_similarity,
                    job.match_scores.skill_overlap,
                    job.match_scores.llm_verification_score,
                    job.skill_analysis.model_dump_json(),
                    job.status,
                ),
            )

    def get_jobs_by_status(self, status: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY composite_match_score DESC",
                (status,),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_job_status(self, job_id: str, status: str):
        with self._connect() as conn:
            conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))

    def get_all_jobs(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY composite_match_score DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Outreach ──

    def insert_outreach(self, result: OutreachResult, email_type: str = "initial"):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO outreach
                   (id, job_id, contact_name, contact_email, contact_title,
                    contact_source, email_subject, email_body, message_id,
                    sent_at, email_type, status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()),
                    result.job_id,
                    result.contact.name,
                    result.contact.email,
                    result.contact.title,
                    result.contact.source,
                    result.email_sent.subject if result.email_sent else "",
                    result.email_sent.body if result.email_sent else "",
                    result.email_sent.message_id if result.email_sent else "",
                    result.email_sent.sent_at if result.email_sent else datetime.utcnow().isoformat(),
                    email_type,
                    result.status,
                ),
            )

    def get_outreach_for_job(self, job_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM outreach WHERE job_id = ? ORDER BY sent_at DESC",
                (job_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_jobs_needing_followup(self, days: int) -> list[dict]:
        """Get jobs where last outreach was > N days ago with no reply."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT j.*, o.sent_at as last_outreach_at,
                          o.email_type as last_email_type, o.id as outreach_id
                   FROM jobs j
                   JOIN outreach o ON j.id = o.job_id
                   LEFT JOIN replies r ON o.id = r.outreach_id
                   WHERE r.id IS NULL
                     AND j.status IN ('awaiting_reply', 'follow_up_1_sent')
                     AND julianday('now') - julianday(o.sent_at) >= ?
                   GROUP BY j.id
                   HAVING o.sent_at = MAX(o.sent_at)""",
                (days,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Replies ──

    def insert_reply(self, reply: ReplyClassification):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO replies
                   (id, outreach_id, from_email, subject, body_snippet,
                    classification, confidence, received_at, processed_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()),
                    reply.outreach_id,
                    reply.from_email,
                    reply.subject,
                    reply.body_snippet,
                    reply.classification,
                    reply.confidence,
                    reply.received_at,
                    datetime.utcnow().isoformat(),
                ),
            )

    def has_reply(self, outreach_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM replies WHERE outreach_id = ?",
                (outreach_id,),
            ).fetchone()
            return row["cnt"] > 0

    # ── Follow-up Queue ──

    def schedule_followup(self, job_id: str, scheduled_at: str, followup_number: int):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO follow_up_queue
                   (id, job_id, scheduled_at, follow_up_number, status)
                   VALUES (?,?,?,?,?)""",
                (str(uuid.uuid4()), job_id, scheduled_at, followup_number, "pending"),
            )

    def get_pending_followups(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM follow_up_queue
                   WHERE status = 'pending'
                     AND julianday('now') >= julianday(scheduled_at)
                   ORDER BY scheduled_at""",
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_followup_sent(self, followup_id: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE follow_up_queue SET status='sent', sent_at=? WHERE id=?",
                (datetime.utcnow().isoformat(), followup_id),
            )

    def get_followup_count(self, job_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM follow_up_queue WHERE job_id=? AND status='sent'",
                (job_id,),
            ).fetchone()
            return row["cnt"]

    # ── Dashboard ──

    def get_status_breakdown(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status"
            ).fetchall()
            return {r["status"]: r["cnt"] for r in rows}

    def get_recent_activity(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT j.id as job_id, j.company, j.title, j.status,
                          COALESCE(o.sent_at, j.scraped_at) as last_action_at
                   FROM jobs j
                   LEFT JOIN outreach o ON j.id = o.job_id
                   ORDER BY last_action_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
