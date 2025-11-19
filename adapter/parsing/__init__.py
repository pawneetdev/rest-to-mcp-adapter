"""
Parsing layer for normalizing API documentation into canonical models.

This module provides:
- Canonical Pydantic models for endpoint representation
- Normalization logic for converting raw data to canonical format
"""

from .canonical_models import (
    CanonicalEndpoint,
    CanonicalParameter,
    CanonicalSchema,
    ParameterLocation,
    DataType,
)
from .normalizer import Normalizer

__all__ = [
    "CanonicalEndpoint",
    "CanonicalParameter",
    "CanonicalSchema",
    "ParameterLocation",
    "DataType",
    "Normalizer",
]
