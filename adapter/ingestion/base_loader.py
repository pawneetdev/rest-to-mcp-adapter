"""
Base loader interface for API documentation ingestion.

This module defines the abstract base class that all concrete loaders must implement.
The loader pattern enables easy extension to support new documentation formats
(Postman, GraphQL, PDF, Markdown, etc.) in future phases.

Design Philosophy:
- Loaders are responsible ONLY for loading and basic validation
- Parsing and normalization happen in separate layers
- Each loader returns raw structured data (dict) or clean text (str)
- Loaders should be resilient to malformed input
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union


class BaseLoader(ABC):
    """
    Abstract base class for all API documentation loaders.

    Concrete implementations must define how to load and validate
    a specific documentation format (OpenAPI, HTML, Postman, etc.).

    The load() method should:
    1. Parse the input content
    2. Perform basic validation
    3. Return structured data (dict) or clean text (str)
    4. Raise descriptive exceptions for invalid input

    Examples:
        >>> class MyCustomLoader(BaseLoader):
        ...     def load(self, content: str) -> dict:
        ...         return json.loads(content)
        ...
        >>> loader = MyCustomLoader()
        >>> result = loader.load('{"api": "spec"}')
    """

    @abstractmethod
    def load(self, content: str) -> Union[Dict[str, Any], str]:
        """
        Load and parse API documentation content.

        Args:
            content: Raw documentation content as string

        Returns:
            Either:
            - dict: Structured data (for formats like OpenAPI, Postman)
            - str: Clean text (for formats like HTML, Markdown, PDF)

        Raises:
            ValueError: If content is invalid or cannot be parsed
            Exception: For format-specific errors (should be caught and wrapped)

        Note:
            Implementations should be defensive and handle:
            - Malformed input gracefully
            - Missing required fields (provide defaults where sensible)
            - Encoding issues
            - Size limits (for very large documents)
        """
        pass

    def validate(self, content: str) -> bool:
        """
        Validate content before loading (optional override).

        This method can be overridden to perform pre-flight validation
        without fully parsing the content.

        Args:
            content: Raw documentation content

        Returns:
            True if content appears valid, False otherwise

        Note:
            Default implementation always returns True.
            Concrete loaders can override for format-specific validation.
        """
        return bool(content and content.strip())

    def __repr__(self) -> str:
        """String representation of the loader."""
        return f"{self.__class__.__name__}()"


class LoaderError(Exception):
    """Base exception for loader-related errors."""

    pass


class InvalidFormatError(LoaderError):
    """Raised when content format is invalid or unsupported."""

    pass


class ValidationError(LoaderError):
    """Raised when content fails validation checks."""

    pass
