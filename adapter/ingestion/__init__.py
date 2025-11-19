"""
Ingestion layer for loading API documentation.

This module provides loaders for different API documentation formats.
Users call the appropriate loader directly for their format.

Available loaders:
- OpenAPILoader: For OpenAPI/Swagger specs (JSON, YAML, URL, file)
- HTMLLoader: For HTML documentation (URL or raw HTML)
"""

from .base_loader import BaseLoader, LoaderError, InvalidFormatError, ValidationError
from .loader_openapi import OpenAPILoader
from .loader_html import HTMLLoader

__all__ = [
    "BaseLoader",
    "LoaderError",
    "InvalidFormatError",
    "ValidationError",
    "OpenAPILoader",
    "HTMLLoader",
]
