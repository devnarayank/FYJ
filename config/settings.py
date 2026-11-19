"""
Centralized application settings loaded from .env file.
"""
import warnings
from pathlib import Path

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from tools.validators import validate_port_number


class OllamaSettings(BaseSettings):
    model: str = Field(default="gpt-oss:120b-cloud", alias="OLLAMA_MODEL")
    base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    enabled: bool = Field(default=True, alias="OLLAMA_ENABLED")

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class GroqSettings(BaseSettings):
    api_key: str = Field(default="", alias="GROQ_API_KEY")
    model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class SmtpSettings(BaseSettings):
    host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    port: int = Field(default=465, alias="SMTP_PORT")
    username: str = Field(default="", alias="SMTP_USERNAME")
    password: str = Field(default="", alias="SMTP_PASSWORD")
    from_name: str = Field(default="", alias="SMTP_FROM_NAME")
    from_email: str = Field(default="", alias="SMTP_FROM_EMAIL")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_assignment=True,
    )

    def validate_port(self) -> int:
        """Validate port number."""
        return validate_port_number(self.port)

    def validate_config(self) -> None:
        """Validate SMTP configuration."""
        # Validate port
        try:
            self.validate_port()
        except ValueError as e:
            raise ValueError(f"Invalid SMTP port: {e}")

        # Validate credentials
        if self.username and not self.password:
            raise ValueError("SMTP password required when username is set")
        if self.password and not self.username:
            raise ValueError("SMTP username required when password is set")


class ImapSettings(BaseSettings):
    host: str = Field(default="imap.gmail.com", alias="IMAP_HOST")
    port: int = Field(default=993, alias="IMAP_PORT")
    username: str = Field(default="", alias="IMAP_USERNAME")
    password: str = Field(default="", alias="IMAP_PASSWORD")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_assignment=True,
    )

    def validate_port(self) -> int:
        """Validate port number."""
        return validate_port_number(self.port)

    def validate_config(self) -> None:
        """Validate IMAP configuration."""
        # Validate port
        try:
            self.validate_port()
        except ValueError as e:
            raise ValueError(f"Invalid IMAP port: {e}")

        # Validate credentials
        if self.username and not self.password:
            raise ValueError("IMAP password required when username is set")
        if self.password and not self.username:
            raise ValueError("IMAP username required when password is set")


class AppSettings(BaseSettings):
    """Master settings — reads .env from project root."""

    # Provider selection
    model_provider: str = Field(default="ollama", alias="MODEL_PROVIDER")
    fallback_model_provider: str = Field(default="groq", alias="FALLBACK_MODEL_PROVIDER")

    # Paths
    db_path: str = Field(default="data/job_hunt.db", alias="DB_PATH")
    chroma_path: str = Field(default="data/chroma_db", alias="CHROMA_PATH")
    resume_dir: str = Field(default="data/resumes", alias="RESUME_DIR")

    # Matching - Stage 1 weights (must sum to 1.0)
    semantic_weight: float = Field(default=0.35, alias="SEMANTIC_WEIGHT", ge=0.0, le=1.0)
    tfidf_weight: float = Field(default=0.30, alias="TFIDF_WEIGHT", ge=0.0, le=1.0)
    skill_overlap_weight: float = Field(default=0.35, alias="SKILL_OVERLAP_WEIGHT", ge=0.0, le=1.0)

    # Matching - Stage 2 weights (must sum to 1.0)
    final_semantic_weight: float = Field(default=0.30, alias="FINAL_SEMANTIC_WEIGHT", ge=0.0, le=1.0)
    final_tfidf_weight: float = Field(default=0.25, alias="FINAL_TFIDF_WEIGHT", ge=0.0, le=1.0)
    final_skill_weight: float = Field(default=0.25, alias="FINAL_SKILL_WEIGHT", ge=0.0, le=1.0)
    llm_verification_weight: float = Field(default=0.20, alias="LLM_VERIFICATION_WEIGHT", ge=0.0, le=1.0)

    # Thresholds
    semantic_pre_filter_threshold: float = Field(default=0.30, alias="SEMANTIC_PRE_FILTER_THRESHOLD", ge=0.0, le=1.0)
    match_threshold: float = Field(default=0.50, alias="MATCH_THRESHOLD", ge=0.0, le=1.0)

    # Score bands (for interpretation labels)
    score_band_strong_min: float = Field(default=0.70, alias="SCORE_BAND_STRONG_MIN", ge=0.0, le=1.0)
    score_band_moderate_min: float = Field(default=0.50, alias="SCORE_BAND_MODERATE_MIN", ge=0.0, le=1.0)

    # Search behavior
    max_results_per_board: int = Field(default=200, alias="MAX_RESULTS_PER_BOARD")
    batch_size: int = Field(default=50, alias="BATCH_SIZE")

    # Job discovery / search layer
    enabled_sources: str = Field(
        default="indeed,linkedin,wellfound,cutshort", alias="ENABLED_SOURCES"
    )
    max_detail_fetches: int = Field(default=20, alias="MAX_DETAIL_FETCHES")
    request_timeout_seconds: int = Field(default=20, alias="REQUEST_TIMEOUT_SECONDS")
    source_failure_threshold: int = Field(default=3, alias="SOURCE_FAILURE_THRESHOLD")
    max_concurrent_fetches: int = Field(default=6, alias="MAX_CONCURRENT_FETCHES")
    min_description_chars: int = Field(default=80, alias="MIN_DESCRIPTION_CHARS")
    jobspy_proxies: str = Field(default="", alias="JOBSPY_PROXIES")

    # Rate limits
    max_emails_per_hour: int = Field(default=10, alias="MAX_EMAILS_PER_HOUR")
    followup_check_interval_minutes: int = Field(default=30, alias="FOLLOWUP_CHECK_INTERVAL_MINUTES")
    days_before_followup: int = Field(default=3, alias="DAYS_BEFORE_FOLLOWUP")
    max_followups: int = Field(default=2, alias="MAX_FOLLOWUPS")

    # Sub-settings
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    groq: GroqSettings = Field(default_factory=GroqSettings)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)
    imap: ImapSettings = Field(default_factory=ImapSettings)

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent

    def ensure_directories(self):
        """Create required data directories if they don't exist."""
        for dir_path in [self.db_path, self.chroma_path, self.resume_dir]:
            path = self.project_root / dir_path
            if "." in Path(dir_path).name:  # It's a file path
                path.parent.mkdir(parents=True, exist_ok=True)
            else:
                path.mkdir(parents=True, exist_ok=True)

    def validate_critical_settings(self) -> None:
        """Validate that critical settings are properly configured."""
        provider = (self.model_provider or "ollama").lower()
        fallback = (self.fallback_model_provider or "groq").lower()

        if provider == "groq" and (not self.groq.api_key or not self.groq.api_key.strip()):
            raise ValueError("GROQ_API_KEY environment variable must be set when using Groq as the primary model.")

        if provider == "ollama" and self.ollama.enabled:
            # Ollama is the preferred free local provider; it should not block startup
            # unless the app is explicitly configured to use a different provider.
            pass
        elif fallback == "groq" and (not self.groq.api_key or not self.groq.api_key.strip()):
            raise ValueError("GROQ_API_KEY environment variable must be set for the fallback provider.")

        # Validate rate limits
        if self.max_emails_per_hour < 1:
            raise ValueError("max_emails_per_hour must be at least 1")

        # Validate Stage 1 weights sum to 1.0
        stage1_sum = self.semantic_weight + self.tfidf_weight + self.skill_overlap_weight
        if abs(stage1_sum - 1.0) > 0.001:
            raise ValueError(
                f"Stage 1 weights sum to {stage1_sum:.3f}, expected 1.0 "
                f"(SEMANTIC_WEIGHT + TFIDF_WEIGHT + SKILL_OVERLAP_WEIGHT)"
            )

        # Validate Stage 2 weights sum to 1.0
        stage2_sum = self.final_semantic_weight + self.final_tfidf_weight + self.final_skill_weight + self.llm_verification_weight
        if abs(stage2_sum - 1.0) > 0.001:
            raise ValueError(
                f"Stage 2 weights sum to {stage2_sum:.3f}, expected 1.0 "
                f"(FINAL_SEMANTIC_WEIGHT + FINAL_TFIDF_WEIGHT + FINAL_SKILL_WEIGHT + LLM_VERIFICATION_WEIGHT)"
            )

        # Validate all weights in [0.0, 1.0] (enforced by Field constraints, but double-check)
        for name, value in [
            ("SEMANTIC_WEIGHT", self.semantic_weight),
            ("TFIDF_WEIGHT", self.tfidf_weight),
            ("SKILL_OVERLAP_WEIGHT", self.skill_overlap_weight),
            ("FINAL_SEMANTIC_WEIGHT", self.final_semantic_weight),
            ("FINAL_TFIDF_WEIGHT", self.final_tfidf_weight),
            ("FINAL_SKILL_WEIGHT", self.final_skill_weight),
            ("LLM_VERIFICATION_WEIGHT", self.llm_verification_weight),
        ]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be between 0.0 and 1.0")

        # Validate thresholds
        if not (0.0 <= self.match_threshold <= 1.0):
            raise ValueError("match_threshold must be between 0.0 and 1.0")
        if not (0.0 <= self.semantic_pre_filter_threshold <= 1.0):
            raise ValueError("semantic_pre_filter_threshold must be between 0.0 and 1.0")
        if not (0.0 <= self.score_band_strong_min <= 1.0):
            raise ValueError("score_band_strong_min must be between 0.0 and 1.0")
        if not (0.0 <= self.score_band_moderate_min <= 1.0):
            raise ValueError("score_band_moderate_min must be between 0.0 and 1.0")

        # Warn if semantic_pre_filter_threshold >= match_threshold (pre-filter too restrictive)
        if self.semantic_pre_filter_threshold >= self.match_threshold:
            warnings.warn(
                f"SEMANTIC_PRE_FILTER_THRESHOLD ({self.semantic_pre_filter_threshold:.2f}) "
                f"should be < MATCH_THRESHOLD ({self.match_threshold:.2f}) for effective pre-filtering",
                UserWarning,
                stacklevel=2
            )

        # Validate score band ordering
        if self.score_band_strong_min <= self.score_band_moderate_min:
            raise ValueError("score_band_strong_min must be > score_band_moderate_min")

        # Validate search layer limits
        if self.max_detail_fetches < 1:
            raise ValueError("max_detail_fetches must be at least 1")
        if self.max_concurrent_fetches < 1:
            raise ValueError("max_concurrent_fetches must be at least 1")
        if self.source_failure_threshold < 1:
            raise ValueError("source_failure_threshold must be at least 1")
        if self.request_timeout_seconds < 1:
            raise ValueError("request_timeout_seconds must be at least 1")
        if self.min_description_chars < 40:
            raise ValueError("min_description_chars must be at least 40")

        # Validate SMTP if credentials are provided
        if self.smtp.username:
            self.smtp.validate_config()

        # Validate IMAP if credentials are provided
        if self.imap.username:
            self.imap.validate_config()


def get_settings() -> AppSettings:
    """Factory function for settings singleton."""
    settings = AppSettings()
    settings.validate_critical_settings()
    return settings
