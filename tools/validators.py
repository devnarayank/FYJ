"""
Input validation utilities for security hardening.
Prevents path traversal, injection attacks, and validates user inputs.
"""
import json
import logging
import re
from pathlib import Path

from email_validator import EmailNotValidError, validate_email

logger = logging.getLogger(__name__)


def parse_json_safely(raw_text: str, fallback: dict | None = None) -> dict:
    """
    Safely parse JSON from text, with fallback to default value.
    Handles common JSON wrapping issues (markdown code blocks, etc).
    
    Args:
        raw_text: Raw text potentially containing JSON
        fallback: Default dict to return on parse failure
        
    Returns:
        Parsed dict or fallback dict
    """
    if fallback is None:
        fallback = {}

    try:
        # Remove markdown code blocks if present
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```", maxsplit=1)[0]
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0]

        # Extract JSON object
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1

        if start == -1 or end == 0:
            logger.warning("No JSON object found in text")
            return fallback

        json_str = raw_text[start:end]
        return json.loads(json_str)

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}. Using fallback.")
        return fallback
    except Exception as e:
        logger.warning(f"Unexpected error parsing JSON: {e}. Using fallback.")
        return fallback


def validate_file_path(file_path: str, allowed_base: str | None = None) -> Path:
    """
    Validate file path to prevent path traversal attacks.
    
    Args:
        file_path: Path to validate
        allowed_base: Optional base directory to restrict paths to
        
    Returns:
        Validated Path object
        
    Raises:
        ValueError: If path is invalid or outside allowed base
    """
    try:
        path = Path(file_path).resolve()

        # Prevent traversal attacks
        if ".." in str(path):
            raise ValueError("Path traversal detected (..) in path")

        # Check if path exists
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {file_path}")

        # If allowed_base is specified, ensure path is within it
        if allowed_base:
            base = Path(allowed_base).resolve()
            try:
                path.relative_to(base)
            except ValueError:
                raise ValueError(f"Path is outside allowed base directory: {file_path}")

        return path
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid file path: {str(e)}")


def validate_email_address(email: str) -> str:
    """
    Validate email address format and structure.
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email address
        
    Raises:
        ValueError: If email is invalid
    """
    try:
        # Validate and normalize
        valid = validate_email(email, check_deliverability=False)
        return valid.email
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email address: {str(e)}")


def validate_directory_path(dir_path: str, create_if_missing: bool = False) -> Path:
    """
    Validate directory path for security.
    
    Args:
        dir_path: Directory path to validate
        create_if_missing: Whether to create directory if it doesn't exist
        
    Returns:
        Validated Path object
        
    Raises:
        ValueError: If path is invalid
    """
    try:
        path = Path(dir_path).resolve()

        # Prevent traversal attacks
        if ".." in str(path):
            raise ValueError("Path traversal detected (..) in path")

        if not path.exists():
            if create_if_missing:
                path.mkdir(parents=True, exist_ok=True)
            else:
                raise FileNotFoundError(f"Directory does not exist: {dir_path}")
        elif not path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")

        return path
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid directory path: {str(e)}")


def validate_url(url: str) -> str:
    """
    Validate URL format and structure.
    
    Args:
        url: URL to validate
        
    Returns:
        Validated URL
        
    Raises:
        ValueError: If URL is invalid
    """
    if not url:
        raise ValueError("URL cannot be empty")

    # Basic URL pattern validation
    url_pattern = r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]{1,2048}$'
    if not re.match(url_pattern, url):
        raise ValueError(f"Invalid URL format: {url}")

    # Prevent common injection patterns
    if any(x in url.lower() for x in ['javascript:', 'data:', '\x00']):
        raise ValueError("Potentially malicious URL format")

    return url


def validate_required_env_vars(required_vars: list[str]) -> dict[str, str]:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: List of environment variable names to check
        
    Returns:
        Dict of {var_name: value} for all required vars
        
    Raises:
        ValueError: If any required variable is missing
    """
    import os

    missing = []
    values = {}

    for var in required_vars:
        value = os.getenv(var)
        if not value or not value.strip():
            missing.append(var)
        else:
            values[var] = value

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return values


def sanitize_sql_identifier(identifier: str) -> str:
    """
    Sanitize SQL identifiers (table/column names).
    Uses allowlist of safe characters.
    
    Args:
        identifier: SQL identifier to sanitize
        
    Returns:
        Sanitized identifier
        
    Raises:
        ValueError: If identifier contains invalid characters
    """
    # Only allow alphanumeric and underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")

    return identifier


def validate_port_number(port: int) -> int:
    """
    Validate port number is within valid range.
    
    Args:
        port: Port number to validate
        
    Returns:
        Validated port number
        
    Raises:
        ValueError: If port is invalid
    """
    if not isinstance(port, int):
        try:
            port = int(port)
        except (ValueError, TypeError):
            raise ValueError(f"Port must be an integer: {port}")

    if not (1 <= port <= 65535):
        raise ValueError(f"Port must be between 1 and 65535: {port}")

    return port


def validate_rate_limit_params(max_per_hour: int, delay_seconds: float) -> tuple[int, float]:
    """
    Validate rate limiting parameters.
    
    Args:
        max_per_hour: Maximum items per hour
        delay_seconds: Delay between operations in seconds
        
    Returns:
        Tuple of (max_per_hour, delay_seconds)
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not isinstance(max_per_hour, int) or max_per_hour < 1:
        raise ValueError(f"max_per_hour must be positive integer: {max_per_hour}")

    if not isinstance(delay_seconds, (int, float)) or delay_seconds < 0:
        raise ValueError(f"delay_seconds must be non-negative: {delay_seconds}")

    return max_per_hour, delay_seconds
