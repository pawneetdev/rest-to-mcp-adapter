"""
Pipeline orchestration for end-to-end API documentation ingestion.

This module provides the high-level entry point for:
- Detecting API documentation formats
- Loading and parsing documentation
- Returning structured output ready for MCP tool generation
"""

from .ingestion_pipeline import ingest_api_source, IngestionResult

__all__ = ["ingest_api_source", "IngestionResult"]
