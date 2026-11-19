"""Unit tests for configuration validation (FR-002, FR-003, FR-004, FR-005, FR-010)."""

import os

import pytest
from pydantic import ValidationError

from config.settings import AppSettings


class TestConfigValidation:
    """Test that AppSettings validates weights and thresholds correctly."""

    def setup_method(self):
        """Clear environment variables before each test."""
        env_vars = [
            "SEMANTIC_WEIGHT", "TFIDF_WEIGHT", "SKILL_OVERLAP_WEIGHT",
            "FINAL_SEMANTIC_WEIGHT", "FINAL_TFIDF_WEIGHT", "FINAL_SKILL_WEIGHT",
            "LLM_VERIFICATION_WEIGHT",
            "SEMANTIC_PRE_FILTER_THRESHOLD", "MATCH_THRESHOLD",
            "SCORE_BAND_STRONG_MIN", "SCORE_BAND_MODERATE_MIN",
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]

    def test_valid_stage1_sum_passes(self):
        """Test that valid Stage 1 weights (sum=1.0) pass validation."""
        os.environ["SEMANTIC_WEIGHT"] = "0.35"
        os.environ["TFIDF_WEIGHT"] = "0.30"
        os.environ["SKILL_OVERLAP_WEIGHT"] = "0.35"
        settings = AppSettings()
        settings.validate_critical_settings()
        assert abs(settings.semantic_weight + settings.tfidf_weight + settings.skill_overlap_weight - 1.0) < 0.001

    def test_valid_stage2_sum_passes(self):
        """Test that valid Stage 2 weights (sum=1.0) pass validation."""
        os.environ["FINAL_SEMANTIC_WEIGHT"] = "0.30"
        os.environ["FINAL_TFIDF_WEIGHT"] = "0.25"
        os.environ["FINAL_SKILL_WEIGHT"] = "0.25"
        os.environ["LLM_VERIFICATION_WEIGHT"] = "0.20"
        settings = AppSettings()
        settings.validate_critical_settings()
        stage2_sum = (
            settings.final_semantic_weight
            + settings.final_tfidf_weight
            + settings.final_skill_weight
            + settings.llm_verification_weight
        )
        assert abs(stage2_sum - 1.0) < 0.001

    def test_stage1_sum_not_one_raises_error(self):
        """Test that Stage 1 weights summing != 1.0 raise clear error with field names."""
        os.environ["SEMANTIC_WEIGHT"] = "0.50"
        os.environ["TFIDF_WEIGHT"] = "0.50"
        os.environ["SKILL_OVERLAP_WEIGHT"] = "0.10"
        settings = AppSettings()
        with pytest.raises(ValueError) as exc_info:
            settings.validate_critical_settings()
        error_msg = str(exc_info.value)
        assert "Stage 1 weights sum to 1.100" in error_msg
        assert "SEMANTIC_WEIGHT" in error_msg
        assert "TFIDF_WEIGHT" in error_msg
        assert "SKILL_OVERLAP_WEIGHT" in error_msg

    def test_stage2_sum_not_one_raises_error(self):
        """Test that Stage 2 weights summing != 1.0 raise clear error with field names."""
        os.environ["FINAL_SEMANTIC_WEIGHT"] = "0.40"
        os.environ["FINAL_TFIDF_WEIGHT"] = "0.40"
        os.environ["FINAL_SKILL_WEIGHT"] = "0.40"
        os.environ["LLM_VERIFICATION_WEIGHT"] = "0.20"
        settings = AppSettings()
        with pytest.raises(ValueError) as exc_info:
            settings.validate_critical_settings()
        error_msg = str(exc_info.value)
        assert "Stage 2 weights sum to 1.400" in error_msg
        assert "FINAL_SEMANTIC_WEIGHT" in error_msg
        assert "FINAL_TFIDF_WEIGHT" in error_msg
        assert "FINAL_SKILL_WEIGHT" in error_msg
        assert "LLM_VERIFICATION_WEIGHT" in error_msg

    def test_negative_weight_raises_error(self):
        """Test that negative weight raises error (caught by Field validation)."""
        os.environ["SEMANTIC_WEIGHT"] = "-0.1"
        os.environ["TFIDF_WEIGHT"] = "0.55"
        os.environ["SKILL_OVERLAP_WEIGHT"] = "0.55"
        with pytest.raises(ValidationError) as exc_info:
            AppSettings()
        error_msg = str(exc_info.value)
        assert "SEMANTIC_WEIGHT" in error_msg
        assert "greater than or equal to 0" in error_msg

    def test_weight_above_one_raises_error(self):
        """Test that weight > 1.0 raises error (caught by Field validation)."""
        os.environ["SEMANTIC_WEIGHT"] = "1.5"
        os.environ["TFIDF_WEIGHT"] = "0.0"
        os.environ["SKILL_OVERLAP_WEIGHT"] = "0.0"
        with pytest.raises(ValidationError) as exc_info:
            AppSettings()
        error_msg = str(exc_info.value)
        assert "SEMANTIC_WEIGHT" in error_msg
        assert "less than or equal to 1" in error_msg

    def test_semantic_pre_filter_threshold_ge_match_threshold_emits_warning(self):
        """Test that semantic_pre_filter_threshold >= match_threshold emits warning."""
        os.environ["SEMANTIC_PRE_FILTER_THRESHOLD"] = "0.60"
        os.environ["MATCH_THRESHOLD"] = "0.50"
        settings = AppSettings()
        with pytest.warns(UserWarning) as record:
            settings.validate_critical_settings()
        assert len(record) == 1
        assert "SEMANTIC_PRE_FILTER_THRESHOLD (0.60)" in str(record[0].message)
        assert "should be < MATCH_THRESHOLD (0.50)" in str(record[0].message)

    def test_score_band_strong_min_le_moderate_min_raises_error(self):
        """Test that score_band_strong_min <= score_band_moderate_min raises error."""
        os.environ["SCORE_BAND_STRONG_MIN"] = "0.50"
        os.environ["SCORE_BAND_MODERATE_MIN"] = "0.70"
        settings = AppSettings()
        with pytest.raises(ValueError) as exc_info:
            settings.validate_critical_settings()
        assert "score_band_strong_min must be > score_band_moderate_min" in str(exc_info.value)

    def test_defaults_match_constants(self):
        """Test that default values match the original constants."""
        settings = AppSettings()
        settings.validate_critical_settings()
        assert settings.semantic_weight == 0.35
        assert settings.tfidf_weight == 0.30
        assert settings.skill_overlap_weight == 0.35
        assert settings.final_semantic_weight == 0.30
        assert settings.final_tfidf_weight == 0.25
        assert settings.final_skill_weight == 0.25
        assert settings.llm_verification_weight == 0.20
        assert settings.semantic_pre_filter_threshold == 0.30
        assert settings.match_threshold == 0.50
        assert settings.score_band_strong_min == 0.70
        assert settings.score_band_moderate_min == 0.50


class TestEnvLoading:
    """Test that .env loading works for all new fields."""

    def test_env_loading_works_for_all_fields(self):
        """Test that each field loads from environment with correct alias."""
        env_vars = {
            "SEMANTIC_WEIGHT": "0.40",
            "TFIDF_WEIGHT": "0.30",
            "SKILL_OVERLAP_WEIGHT": "0.30",
            "FINAL_SEMANTIC_WEIGHT": "0.35",
            "FINAL_TFIDF_WEIGHT": "0.25",
            "FINAL_SKILL_WEIGHT": "0.20",
            "LLM_VERIFICATION_WEIGHT": "0.20",
            "SEMANTIC_PRE_FILTER_THRESHOLD": "0.25",
            "MATCH_THRESHOLD": "0.55",
            "SCORE_BAND_STRONG_MIN": "0.75",
            "SCORE_BAND_MODERATE_MIN": "0.55",
        }
        for key, value in env_vars.items():
            os.environ[key] = value

        settings = AppSettings()
        settings.validate_critical_settings()

        assert settings.semantic_weight == 0.40
        assert settings.tfidf_weight == 0.30
        assert settings.skill_overlap_weight == 0.30
        assert settings.final_semantic_weight == 0.35
        assert settings.final_tfidf_weight == 0.25
        assert settings.final_skill_weight == 0.20
        assert settings.llm_verification_weight == 0.20
        assert settings.semantic_pre_filter_threshold == 0.25
        assert settings.match_threshold == 0.55
        assert settings.score_band_strong_min == 0.75
        assert settings.score_band_moderate_min == 0.55

        # Clean up
        for key in env_vars:
            del os.environ[key]
