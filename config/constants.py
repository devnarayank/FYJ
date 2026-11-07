"""
Application-wide constants and thresholds.
"""

# --- Matching Pipeline Weights ---
# Stage 1 (pre-screening, before the LLM verification call).
SEMANTIC_WEIGHT = 0.35
TFIDF_WEIGHT = 0.30
SKILL_OVERLAP_WEIGHT = 0.35

# Stage 2 (final composite, includes the LLM verification score).
FINAL_SEMANTIC_WEIGHT = 0.30
FINAL_TFIDF_WEIGHT = 0.25
FINAL_SKILL_WEIGHT = 0.25
LLM_VERIFICATION_WEIGHT = 0.20

# Loose gate for Stage 1 (semantic pre-filter)
SEMANTIC_PRE_FILTER_THRESHOLD = 0.50

# --- Job Sources ---
# Boards reachable through the JobSpy scraper. Several of them answer every
# request with a bot-protection wall (HTTP 403), so only the ones that
# actually serve results are enabled by default. The rest stay selectable and
# are disabled automatically for the run if they keep failing.
JOBSPY_BOARDS = [
    "indeed",
    "linkedin",
    "glassdoor",
    "zip_recruiter",
    "bayt",
    "naukri",
]

#: JobSpy boards that are known to work without a proxy.
WORKING_JOBSPY_BOARDS = ["indeed", "linkedin"]

#: Boards scraped directly over HTTP by the provider layer. Each of them
#: publishes a schema.org JobPosting document for every posting.
DIRECT_BOARDS = ["wellfound", "cutshort"]

NICHE_JOB_PLATFORMS = {
    "wellfound": {
        "name": "Wellfound",
        "search_url": "https://wellfound.com/jobs?q={query}",
        "best_for": "Startup jobs for developers and AI engineers",
        "why_better": "Startup jobs posted directly by companies and real hiring teams",
    },
    "cutshort": {
        "name": "CutShort",
        "search_url": "https://cutshort.io/jobs/{query}-jobs",
        "best_for": "Indian tech market, software engineers, data scientists",
        "why_better": "AI-powered matching, direct company outreach, less agency spam",
    },
}

SUPPORTED_BOARDS = JOBSPY_BOARDS + DIRECT_BOARDS
DEFAULT_BOARDS = WORKING_JOBSPY_BOARDS + DIRECT_BOARDS

# --- Rate Limiting ---
SCRAPE_DELAY_SECONDS = 2.0       # Delay between job board requests
EMAIL_DELAY_SECONDS = 360        # 6 min between emails (10/hour)
GROQ_DELAY_SECONDS = 2.0         # Respect Groq free-tier rate limits

# --- Email ---
MAX_EMAIL_BODY_WORDS = 150
MAX_SUBJECT_LENGTH = 60

# --- Follow-up ---
BUSINESS_DAYS_BEFORE_FOLLOWUP = 3
MAX_FOLLOWUP_COUNT = 2

# --- Application Statuses ---
STATUS_MATCHED = "matched"
STATUS_APPLIED = "applied"
STATUS_AWAITING_REPLY = "awaiting_reply"
STATUS_REPLIED_POSITIVE = "replied_positive"
STATUS_REPLIED_NEGATIVE = "replied_negative"
STATUS_FOLLOWUP_1 = "follow_up_1_sent"
STATUS_FOLLOWUP_2 = "follow_up_2_sent"
STATUS_COLD = "cold"
STATUS_INTERVIEW = "interview_scheduled"

ALL_STATUSES = [
    STATUS_MATCHED, STATUS_APPLIED, STATUS_AWAITING_REPLY,
    STATUS_REPLIED_POSITIVE, STATUS_REPLIED_NEGATIVE,
    STATUS_FOLLOWUP_1, STATUS_FOLLOWUP_2, STATUS_COLD, STATUS_INTERVIEW,
]

# --- HTTP Headers ---
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
