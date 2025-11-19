"""
Simplified ingestion helpers for API documentation.

This module provides convenience functions for common workflows,
but users typically call loaders directly for more control.

Direct usage is recommended:
    >>> from adapter.ingestion import OpenAPILoader, HTMLLoader
    >>> loader = OpenAPILoader()
    >>> spec = loader.load("https://api.example.com/openapi.json")

Or use these helper functions for quick prototyping:
    >>> from adapter.pipeline import load_openapi, load_html
    >>> spec = load_openapi("https://api.example.com/openapi.json")
"""

from typing import Any, Dict

from ..ingestion import OpenAPILoader, HTMLLoader


def load_openapi(
    source: str,
    strict: bool = False,
    use_langchain: bool = True,
) -> Dict[str, Any]:
    """
    Convenience function to load OpenAPI specification.

    This is a simplified wrapper around OpenAPILoader for quick usage.
    For more control, use OpenAPILoader directly.

    Args:
        source: URL, file path, or raw OpenAPI content (JSON/YAML)
        strict: Enable strict validation (default: False)
        use_langchain: Use LangChain utilities if available (default: True)

    Returns:
        Parsed OpenAPI specification as dictionary

    Examples:
        >>> # Load from URL
        >>> spec = load_openapi("https://api.example.com/openapi.json")

        >>> # Load from file
        >>> spec = load_openapi("./specs/api.yaml")

        >>> # Load from raw content
        >>> spec = load_openapi('{"openapi": "3.0.0", ...}')

        >>> # With strict validation
        >>> spec = load_openapi("api.yaml", strict=True)
    """
    loader = OpenAPILoader(strict=strict, use_langchain=use_langchain)
    return loader.load(source)


def load_html(
    source: str,
    use_langchain: bool = True,
    preserve_structure: bool = True,
) -> str:
    """
    Convenience function to load and clean HTML documentation.

    This is a simplified wrapper around HTMLLoader for quick usage.
    For more control, use HTMLLoader directly.

    Args:
        source: URL or raw HTML content
        use_langchain: Use LangChain utilities if available (default: True)
        preserve_structure: Preserve headings and structure markers (default: True)

    Returns:
        Clean text extracted from HTML

    Examples:
        >>> # Load from URL
        >>> text = load_html("https://docs.example.com/api")

        >>> # Load from raw HTML
        >>> text = load_html("<html><body>API Docs</body></html>")
    """
    loader = HTMLLoader(
        use_langchain=use_langchain,
        preserve_structure=preserve_structure,
    )

    # Check if it's a URL or raw HTML
    if source.strip().startswith(("http://", "https://")):
        return loader.load_from_url(source)
    else:
        return loader.load(source)
