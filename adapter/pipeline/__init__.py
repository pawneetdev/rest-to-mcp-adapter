"""
Pipeline helpers for API documentation ingestion.

This module provides convenience functions for quick prototyping.
For production use, call loaders directly from adapter.ingestion.
"""

from .ingestion_pipeline import load_openapi, load_html

__all__ = ["load_openapi", "load_html"]
