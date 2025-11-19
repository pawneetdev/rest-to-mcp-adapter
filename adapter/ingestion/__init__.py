"""
Ingestion layer for loading and detecting API documentation formats.

This module provides:
- Format detection capabilities
- Base loader interface
- Concrete loaders for OpenAPI and HTML formats
"""

from .base_loader import BaseLoader
from .detector import FormatDetector, APIFormat
from .loader_openapi import OpenAPILoader
from .loader_html import HTMLLoader

__all__ = [
    "BaseLoader",
    "FormatDetector",
    "APIFormat",
    "OpenAPILoader",
    "HTMLLoader",
]
