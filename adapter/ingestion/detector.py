"""
Format detection for API documentation.

This module provides automatic detection of API documentation formats
based on content analysis and optional filename hints.

Supported formats:
- OpenAPI/Swagger (JSON and YAML)
- HTML documentation
- Unknown (fallback)

Future formats (not yet implemented):
- Postman collections
- GraphQL schemas
- Markdown documentation
- PDF documentation
"""

import json
import re
from enum import Enum
from typing import Optional

import yaml


class APIFormat(str, Enum):
    """Enumeration of supported API documentation formats."""

    OPENAPI = "openapi"
    HTML = "html"
    UNKNOWN = "unknown"
    # Future formats (for extensibility):
    # POSTMAN = "postman"
    # GRAPHQL = "graphql"
    # MARKDOWN = "markdown"
    # PDF = "pdf"


class FormatDetector:
    """
    Intelligent format detection for API documentation.

    Uses multiple detection strategies:
    1. Filename extension (if provided)
    2. Content structure analysis
    3. Format-specific markers and patterns

    Examples:
        >>> detector = FormatDetector()
        >>> fmt = detector.detect(content='{"openapi": "3.0.0"}')
        >>> print(fmt)
        APIFormat.OPENAPI

        >>> fmt = detector.detect(filename="api.yaml", content="openapi: 3.0.0")
        >>> print(fmt)
        APIFormat.OPENAPI

        >>> fmt = detector.detect(content="<html><body>API Docs</body></html>")
        >>> print(fmt)
        APIFormat.HTML
    """

    # File extension to format mapping
    EXTENSION_MAP = {
        ".json": APIFormat.OPENAPI,  # Assume JSON is OpenAPI by default
        ".yaml": APIFormat.OPENAPI,
        ".yml": APIFormat.OPENAPI,
        ".html": APIFormat.HTML,
        ".htm": APIFormat.HTML,
        # Future:
        # ".md": APIFormat.MARKDOWN,
        # ".pdf": APIFormat.PDF,
    }

    def detect(
        self,
        content: str,
        filename: Optional[str] = None,
    ) -> APIFormat:
        """
        Detect the format of API documentation.

        Args:
            content: The documentation content as a string
            filename: Optional filename to use as a hint

        Returns:
            APIFormat enum indicating the detected format

        Note:
            Detection priority:
            1. Try filename extension first (if provided)
            2. Analyze content structure
            3. Fall back to UNKNOWN if uncertain
        """
        if not content or not content.strip():
            return APIFormat.UNKNOWN

        # Strategy 1: Filename extension hint
        if filename:
            ext_format = self._detect_by_extension(filename)
            if ext_format != APIFormat.UNKNOWN:
                # Verify the extension hint matches content
                if self._verify_format(content, ext_format):
                    return ext_format

        # Strategy 2: Content analysis
        return self._detect_by_content(content)

    def _detect_by_extension(self, filename: str) -> APIFormat:
        """Detect format based on file extension."""
        filename_lower = filename.lower()
        for ext, fmt in self.EXTENSION_MAP.items():
            if filename_lower.endswith(ext):
                return fmt
        return APIFormat.UNKNOWN

    def _detect_by_content(self, content: str) -> APIFormat:
        """
        Detect format by analyzing content structure and markers.

        Detection strategies:
        - OpenAPI: Look for "openapi" or "swagger" fields in JSON/YAML
        - HTML: Look for HTML tags
        - Unknown: Default fallback
        """
        content_stripped = content.strip()

        # Check for OpenAPI/Swagger (JSON or YAML)
        if self._is_openapi(content_stripped):
            return APIFormat.OPENAPI

        # Check for HTML
        if self._is_html(content_stripped):
            return APIFormat.HTML

        # Default fallback
        return APIFormat.UNKNOWN

    def _is_openapi(self, content: str) -> bool:
        """
        Check if content appears to be OpenAPI/Swagger spec.

        Looks for:
        - "openapi" field (OpenAPI 3.x)
        - "swagger" field (Swagger 2.x)
        - "paths" field (common to both)
        """
        try:
            # Try parsing as JSON
            data = json.loads(content)
            return self._has_openapi_markers(data)
        except (json.JSONDecodeError, ValueError):
            pass

        try:
            # Try parsing as YAML
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                return self._has_openapi_markers(data)
        except (yaml.YAMLError, ValueError):
            pass

        return False

    def _has_openapi_markers(self, data: dict) -> bool:
        """Check if parsed data contains OpenAPI/Swagger markers."""
        if not isinstance(data, dict):
            return False

        # OpenAPI 3.x has "openapi" field
        if "openapi" in data:
            return True

        # Swagger 2.x has "swagger" field
        if "swagger" in data:
            return True

        # Both should have "paths" field (though this alone is not definitive)
        # We require paths AND (info OR host OR basePath) for higher confidence
        if "paths" in data:
            if any(key in data for key in ["info", "host", "basePath", "servers"]):
                return True

        return False

    def _is_html(self, content: str) -> bool:
        """
        Check if content appears to be HTML.

        Uses multiple heuristics:
        1. Starts with HTML-like tags
        2. Contains common HTML structure markers
        3. Has HTML doctype declaration
        """
        content_lower = content.lower()

        # Check for DOCTYPE
        if content_lower.startswith("<!doctype html"):
            return True

        # Check for opening HTML tag
        if re.match(r"^\s*<html[\s>]", content_lower):
            return True

        # Check for common HTML tags in the beginning
        html_tag_pattern = r"^\s*<(!DOCTYPE|html|head|body|div|meta)"
        if re.match(html_tag_pattern, content_lower, re.IGNORECASE):
            return True

        # Check for presence of multiple HTML tags
        html_tags = ["<html", "<head", "<body", "<div", "<span", "<p", "<a"]
        tag_count = sum(1 for tag in html_tags if tag in content_lower)
        if tag_count >= 3:
            return True

        return False

    def _verify_format(self, content: str, expected_format: APIFormat) -> bool:
        """
        Verify that content matches the expected format.

        This is used to validate filename hints against actual content.

        Args:
            content: The documentation content
            expected_format: The format suggested by filename

        Returns:
            True if content matches expected format, False otherwise
        """
        detected_format = self._detect_by_content(content)

        # If we can't detect format from content, trust the filename
        if detected_format == APIFormat.UNKNOWN:
            return True

        # Otherwise, they should match
        return detected_format == expected_format
