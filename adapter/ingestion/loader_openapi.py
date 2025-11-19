"""
OpenAPI/Swagger specification loader with URL and file path support.

This loader handles:
- OpenAPI 3.x specifications
- Swagger 2.x specifications
- Both JSON and YAML formats
- Loading from URLs, file paths, or raw content
- Partial/malformed specs (with graceful degradation)

The loader leverages LangChain's OpenAPISpec utility for parsing and validation
when available, with a fallback to manual parsing for flexibility.

Design notes:
- Supports URLs, file paths, and raw content
- Prefers LangChain utilities for standardization
- Resilient to missing or malformed fields
- Returns structured dict ready for normalization
"""

import json
from pathlib import Path
from typing import Any, Dict, Union
from urllib.parse import urlparse

import yaml

from .base_loader import BaseLoader, InvalidFormatError, ValidationError


class OpenAPILoader(BaseLoader):
    """
    Loader for OpenAPI and Swagger specifications.

    This loader can parse both OpenAPI 3.x and Swagger 2.x specifications
    in JSON or YAML format. It supports loading from:
    - URLs (http/https)
    - File paths (local filesystem)
    - Raw content strings

    It uses LangChain's OpenAPISpec when available for robust parsing,
    but can also handle specs manually.

    The loader is designed to be resilient:
    - Handles partial specs
    - Provides sensible defaults for missing fields
    - Validates required fields while being lenient with optional ones

    Examples:
        >>> # Load from URL
        >>> loader = OpenAPILoader()
        >>> spec = loader.load_from_url("https://api.example.com/openapi.json")
        >>> print(spec.keys())
        dict_keys(['openapi', 'info', 'paths', ...])

        >>> # Load from file path
        >>> spec = loader.load_from_file("./specs/api.yaml")

        >>> # Load from raw content
        >>> spec = loader.load(openapi_yaml_content)

        >>> # With strict validation
        >>> loader = OpenAPILoader(strict=True)
        >>> spec = loader.load(malformed_spec)  # Raises ValidationError
    """

    def __init__(self, strict: bool = False, use_langchain: bool = True):
        """
        Initialize the OpenAPI loader.

        Args:
            strict: If True, enforce strict validation (default: False)
            use_langchain: If True, prefer LangChain utilities (default: True)
        """
        self.strict = strict
        self.use_langchain = use_langchain

    def load_from_url(self, url: str) -> Dict[str, Any]:
        """
        Load OpenAPI spec from a URL.

        Args:
            url: URL to the OpenAPI specification (JSON or YAML)

        Returns:
            Parsed specification as a dictionary

        Raises:
            InvalidFormatError: If URL is invalid or content cannot be fetched
            ValueError: If URL scheme is not http/https

        Examples:
            >>> loader = OpenAPILoader()
            >>> spec = loader.load_from_url("https://api.example.com/openapi.json")
        """
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme in ["http", "https"]:
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Use http or https.")

        if not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")

        # Fetch content
        try:
            import requests

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

        except ImportError:
            raise InvalidFormatError(
                "requests library not available. Install with: uv add requests"
            )
        except requests.RequestException as e:
            raise InvalidFormatError(f"Failed to fetch URL {url}: {e}")

        # Parse and return
        return self.load(content)

    def load_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load OpenAPI spec from a file path.

        Args:
            file_path: Path to the OpenAPI specification file

        Returns:
            Parsed specification as a dictionary

        Raises:
            InvalidFormatError: If file cannot be read
            FileNotFoundError: If file does not exist

        Examples:
            >>> loader = OpenAPILoader()
            >>> spec = loader.load_from_file("./api/openapi.yaml")
            >>> spec = loader.load_from_file(Path("specs/api.json"))
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise InvalidFormatError(f"Not a file: {file_path}")

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise InvalidFormatError(f"Failed to read file {file_path}: {e}")

        # Parse and return
        return self.load(content)

    def load(self, content: str) -> Dict[str, Any]:
        """
        Load and parse OpenAPI/Swagger specification from raw content.

        This method intelligently detects if the content is:
        - A URL (starts with http:// or https://)
        - A file path (exists on filesystem)
        - Raw JSON/YAML content

        Args:
            content: OpenAPI spec as JSON/YAML string, URL, or file path

        Returns:
            Parsed specification as a dictionary

        Raises:
            InvalidFormatError: If content is not valid OpenAPI/Swagger
            ValidationError: If strict=True and spec is malformed

        Examples:
            >>> loader = OpenAPILoader()
            >>> # From URL
            >>> spec = loader.load("https://api.example.com/openapi.json")
            >>> # From file path
            >>> spec = loader.load("./specs/api.yaml")
            >>> # From raw content
            >>> spec = loader.load('{"openapi": "3.0.0", ...}')
        """
        if not content or not content.strip():
            raise InvalidFormatError("Content cannot be empty")

        content_stripped = content.strip()

        # Check if it's a URL (do this first, before file path check)
        if content_stripped.startswith(("http://", "https://")):
            return self.load_from_url(content_stripped)

        # Check if it's a file path (only for reasonable length strings)
        # Avoid "File name too long" errors for very long strings
        if len(content_stripped) < 4096:  # Max path length on most systems
            try:
                file_path = Path(content_stripped)
                if file_path.exists() and file_path.is_file():
                    return self.load_from_file(file_path)
            except (OSError, ValueError):
                # Not a valid file path, continue to treat as raw content
                pass

        # Otherwise, treat as raw content
        return self._load_from_content(content)

    def _load_from_content(self, content: str) -> Dict[str, Any]:
        """
        Internal method to load from raw content string.

        Args:
            content: Raw OpenAPI spec as JSON or YAML string

        Returns:
            Parsed specification as a dictionary

        Raises:
            InvalidFormatError: If content is not valid OpenAPI/Swagger
            ValidationError: If strict=True and spec is malformed
        """
        if not self.validate(content):
            raise InvalidFormatError("Content appears to be empty or invalid")

        # Parse the content (JSON or YAML)
        spec_dict = self._parse_content(content)

        # Try LangChain integration first if enabled
        if self.use_langchain:
            try:
                spec_dict = self._load_with_langchain(spec_dict)
            except ImportError:
                # LangChain not available, fall back to manual parsing
                pass
            except Exception as e:
                # LangChain failed, fall back to manual parsing
                if self.strict:
                    raise ValidationError(f"LangChain validation failed: {e}")

        # Validate the spec structure
        self._validate_spec(spec_dict)

        return spec_dict

    def _parse_content(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON or YAML content into a dictionary.

        Args:
            content: Raw content string

        Returns:
            Parsed dictionary

        Raises:
            InvalidFormatError: If content cannot be parsed
        """
        content_stripped = content.strip()

        # Try JSON first (faster)
        if content_stripped.startswith("{"):
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise InvalidFormatError(f"Invalid JSON: {e}")

        # Try YAML
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                raise InvalidFormatError(
                    f"Expected dict, got {type(data).__name__}"
                )
            return data
        except yaml.YAMLError as e:
            raise InvalidFormatError(f"Invalid YAML: {e}")

    def _load_with_langchain(self, spec_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load spec using LangChain's OpenAPISpec utility.

        This provides additional validation and normalization.

        Args:
            spec_dict: Parsed OpenAPI spec

        Returns:
            Validated and normalized spec dictionary

        Raises:
            ImportError: If LangChain is not installed
        """
        try:
            from langchain_community.utilities.openapi import OpenAPISpec

            # Create OpenAPISpec instance from dict
            # Note: OpenAPISpec expects the spec as a dict
            openapi_spec = OpenAPISpec.from_spec_dict(spec_dict)

            # Return the underlying spec dict
            # OpenAPISpec provides validation and normalization
            return openapi_spec.spec_dict

        except ImportError:
            raise ImportError(
                "LangChain not available. Install with: "
                "uv add langchain-community"
            )

    def _validate_spec(self, spec_dict: Dict[str, Any]) -> None:
        """
        Validate OpenAPI/Swagger spec structure.

        Checks for required fields based on OpenAPI 3.x and Swagger 2.x specs.

        Args:
            spec_dict: Parsed spec dictionary

        Raises:
            ValidationError: If required fields are missing (in strict mode)
        """
        if not isinstance(spec_dict, dict):
            raise ValidationError("Spec must be a dictionary")

        # Check for version field
        has_openapi = "openapi" in spec_dict
        has_swagger = "swagger" in spec_dict

        if not has_openapi and not has_swagger:
            if self.strict:
                raise ValidationError(
                    "Spec must contain 'openapi' or 'swagger' version field"
                )

        # Check for required fields
        required_fields = ["info"]  # 'info' is required in both OpenAPI and Swagger

        # 'paths' is technically required, but we allow it to be missing
        # for partial/incomplete specs (common in documentation)
        if self.strict and "paths" not in spec_dict:
            raise ValidationError("Spec must contain 'paths' field")

        for field in required_fields:
            if field not in spec_dict:
                if self.strict:
                    raise ValidationError(f"Missing required field: {field}")
                else:
                    # Provide default for missing fields
                    if field == "info":
                        spec_dict["info"] = {"title": "Unknown API", "version": "1.0.0"}

        # Validate info field structure
        if "info" in spec_dict:
            info = spec_dict["info"]
            if not isinstance(info, dict):
                raise ValidationError("'info' field must be a dictionary")

            if self.strict:
                if "title" not in info:
                    raise ValidationError("'info' must contain 'title'")
                if "version" not in info:
                    raise ValidationError("'info' must contain 'version'")

    def validate(self, content: str) -> bool:
        """
        Pre-flight validation of content.

        Args:
            content: Raw content string

        Returns:
            True if content appears to be valid OpenAPI/Swagger
        """
        if not content or not content.strip():
            return False

        try:
            spec_dict = self._parse_content(content)

            # Quick check for OpenAPI/Swagger markers
            if "openapi" in spec_dict or "swagger" in spec_dict:
                return True

            # Also accept if it has 'paths' (might be partial spec)
            if "paths" in spec_dict:
                return True

        except (InvalidFormatError, Exception):
            return False

        return False
