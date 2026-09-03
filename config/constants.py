"""
Application-wide constants and thresholds.
"""

# --- Matching Pipeline Weights ---
SEMANTIC_WEIGHT = 0.35
TFIDF_WEIGHT = 0.30
SKILL_OVERLAP_WEIGHT = 0.35

# Loose gate for Stage 1 (semantic pre-filter)
SEMANTIC_PRE_FILTER_THRESHOLD = 0.50

# --- Job Boards ---
JOBSPY_BOARDS = ["indeed", "linkedin", "glassdoor", "zip_recruiter"]

NICHE_JOB_PLATFORMS = {
    "cutshort": {
        "name": "CutShort",
        "search_url": "https://cutshort.io/jobs/{query}-jobs",
        "best_for": "Indian tech market, software engineers, data scientists",
        "why_better": "AI-powered matching, direct company outreach, less agency spam",
    },
    "wellfound": {
        "name": "Wellfound",
        "search_url": "https://wellfound.com/jobs?q={query}",
        "best_for": "Startup jobs for developers and AI engineers",
        "why_better": "Startup jobs posted directly by companies and real hiring teams",
    },
    "instahyre": {
        "name": "Instahyre",
        "search_url": "https://www.instahyre.com/search-jobs/?search={query}",
        "best_for": "Software engineers and data engineers in India",
        "why_better": "Privacy-focused direct company hiring for premium tech roles",
    },
    "analytics_vidhya": {
        "name": "Analytics Vidhya Career Portal",
        "search_url": "https://jobs.analyticsvidhya.com/jobs/?q={query}",
        "best_for": "Data scientists, AI researchers, ML engineers",
        "why_better": "Niche AI and analytics hiring with community-driven roles",
    },
    "huggingface": {
        "name": "Hugging Face Jobs",
        "search_url": "https://huggingface.co/jobs?search={query}",
        "best_for": "AI engineers, AI researchers, ML roles",
        "why_better": "AI/ML-specific roles from AI-focused companies",
    },
    "triplebyte": {
        "name": "Triplebyte",
        "search_url": "https://triplebyte.com/jobs?query={query}",
        "best_for": "Software engineers and data engineers",
        "why_better": "Assessment-led company interviews with fewer agency interactions",
    },
    "otta": {
        "name": "Otta",
        "search_url": "https://app.otta.com/jobs?query={query}",
        "best_for": "Tech roles at startups for developers and data specialists",
        "why_better": "Curated tech companies and high-quality startup roles",
    },
}

SUPPORTED_BOARDS = JOBSPY_BOARDS + list(NICHE_JOB_PLATFORMS.keys())
DEFAULT_BOARDS = SUPPORTED_BOARDS

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
