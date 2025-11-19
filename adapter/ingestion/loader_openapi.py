"""
OpenAPI/Swagger specification loader with LangChain integration.

This loader handles:
- OpenAPI 3.x specifications
- Swagger 2.x specifications
- Both JSON and YAML formats
- Partial/malformed specs (with graceful degradation)

The loader leverages LangChain's OpenAPISpec utility for parsing and validation
when available, with a fallback to manual parsing for flexibility.

Design notes:
- Prefers LangChain utilities for standardization
- Resilient to missing or malformed fields
- Returns structured dict ready for normalization
"""

import json
from typing import Any, Dict, Union

import yaml

from .base_loader import BaseLoader, InvalidFormatError, ValidationError


class OpenAPILoader(BaseLoader):
    """
    Loader for OpenAPI and Swagger specifications.

    This loader can parse both OpenAPI 3.x and Swagger 2.x specifications
    in JSON or YAML format. It uses LangChain's OpenAPISpec when available
    for robust parsing, but can also handle specs manually.

    The loader is designed to be resilient:
    - Handles partial specs
    - Provides sensible defaults for missing fields
    - Validates required fields while being lenient with optional ones

    Examples:
        >>> loader = OpenAPILoader()
        >>> spec = loader.load(openapi_yaml_content)
        >>> print(spec.keys())
        dict_keys(['openapi', 'info', 'paths', ...])

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

    def load(self, content: str) -> Dict[str, Any]:
        """
        Load and parse OpenAPI/Swagger specification.

        Args:
            content: OpenAPI spec as JSON or YAML string

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
                "pip install langchain-community"
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
