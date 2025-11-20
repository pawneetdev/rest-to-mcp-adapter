"""
Canonical data models for normalized API endpoint representation.

These Pydantic models define a unified schema for representing REST API endpoints
regardless of the source documentation format (OpenAPI, Postman, HTML, etc.).

The canonical format ensures consistency and enables straightforward conversion
to MCP tool definitions in later phases.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DataType(str, Enum):
    """Normalized data types for parameters and schemas."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NULL = "null"


class ParameterLocation(str, Enum):
    """Normalized parameter locations."""

    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    BODY = "body"
    COOKIE = "cookie"


class CanonicalSchema(BaseModel):
    """
    Represents a JSON schema for request/response bodies.

    This is a simplified schema representation that captures the essential
    structure needed for MCP tool generation.
    """

    type: DataType = Field(..., description="The primary data type")
    properties: Optional[Dict[str, "CanonicalSchema"]] = Field(
        default=None,
        description="Properties for object types (nested schema)",
    )
    items: Optional["CanonicalSchema"] = Field(
        default=None,
        description="Item schema for array types",
    )
    required: Optional[List[str]] = Field(
        default=None,
        description="Required property names for object types",
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description",
    )
    example: Optional[Any] = Field(
        default=None,
        description="Example value",
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class CanonicalParameter(BaseModel):
    """
    Represents a single API parameter (query, path, header, or body field).

    This model normalizes parameter definitions from various source formats
    into a consistent structure.
    """

    name: str = Field(..., description="Parameter name in snake_case")
    location: ParameterLocation = Field(
        ..., description="Where the parameter is sent"
    )
    type: DataType = Field(..., description="Parameter data type")
    required: bool = Field(default=False, description="Whether parameter is required")
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description",
    )
    default: Optional[Any] = Field(
        default=None,
        description="Default value if not provided",
    )
    example: Optional[Any] = Field(
        default=None,
        description="Example value",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure parameter names are in snake_case."""
        if not v:
            raise ValueError("Parameter name cannot be empty")
        return v.strip()

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class CanonicalEndpoint(BaseModel):
    """
    Canonical representation of a REST API endpoint.

    This is the primary data structure used throughout the adapter.
    All API documentation formats are normalized into this structure.

    Fields:
        name: A unique, snake_case identifier for the endpoint
        method: HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
        path: URL path with parameter placeholders (e.g., /users/{user_id})
        description: Human-readable description of what the endpoint does
        parameters: List of all parameters (query, path, header)
        body_schema: Optional schema for request body
        response_schema: Optional schema for successful response
        tags: Optional categorization tags
        summary: Optional brief summary (shorter than description)
    """

    name: str = Field(
        ...,
        description="Unique endpoint identifier in snake_case",
    )
    method: str = Field(
        ...,
        description="HTTP method (uppercase)",
    )
    path: str = Field(
        ...,
        description="URL path with {param} placeholders",
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description of endpoint functionality",
    )
    summary: Optional[str] = Field(
        default=None,
        description="Brief summary (one line)",
    )
    parameters: List[CanonicalParameter] = Field(
        default_factory=list,
        description="All parameters for this endpoint",
    )
    body_schema: Optional[CanonicalSchema] = Field(
        default=None,
        description="Request body schema",
    )
    response_schema: Optional[CanonicalSchema] = Field(
        default=None,
        description="Successful response schema (usually 200/201)",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Categorization tags",
    )
    security: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Security requirements (empty list = public endpoint)",
    )
    deprecated: bool = Field(
        default=False,
        description="Whether this endpoint is deprecated",
    )

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Ensure HTTP method is uppercase."""
        if not v:
            raise ValueError("HTTP method cannot be empty")
        return v.upper().strip()

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Ensure path starts with /."""
        if not v:
            raise ValueError("Path cannot be empty")
        v = v.strip()
        if not v.startswith("/"):
            v = f"/{v}"
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v:
            raise ValueError("Endpoint name cannot be empty")
        return v.strip()

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


# Enable forward references for recursive schemas
CanonicalSchema.model_rebuild()
