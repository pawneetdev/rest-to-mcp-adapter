"""
Normalization layer for converting raw API data to canonical format.

This module transforms raw endpoint data from various sources (OpenAPI, LLM-extracted
HTML, Postman, etc.) into the canonical CanonicalEndpoint format.

Key responsibilities:
- Name normalization (snake_case conversion)
- Type system normalization (string, number, boolean, object, array)
- Parameter location normalization (query, path, header, body)
- Schema transformation to CanonicalSchema format
- Providing safe defaults for missing fields

The normalizer is designed to handle:
- OpenAPI/Swagger specs (structured data)
- LLM-extracted endpoints (future phase)
- Partial/incomplete endpoint definitions
"""

import re
import logging
from typing import Any, Dict, List, Optional

from .canonical_models import (
    CanonicalEndpoint,
    CanonicalParameter,
    CanonicalSchema,
    DataType,
    ParameterLocation,
)

logger = logging.getLogger(__name__)


class Normalizer:
    """
    Normalizes raw API endpoint data into canonical format.

    This class provides methods to convert endpoint definitions from
    various sources into the standardized CanonicalEndpoint model.

    Examples:
        >>> normalizer = Normalizer()
        >>> endpoints = normalizer.normalize_openapi(openapi_spec)
        >>> for endpoint in endpoints:
        ...     print(endpoint.name, endpoint.method, endpoint.path)

        >>> # Single endpoint normalization
        >>> raw_endpoint = {
        ...     "method": "GET",
        ...     "path": "/users/{userId}",
        ...     "description": "Get user by ID"
        ... }
        >>> endpoint = normalizer.normalize_endpoint(raw_endpoint)
    """

    # Type mapping from OpenAPI/JSON Schema to canonical types
    TYPE_MAPPING = {
        "string": DataType.STRING,
        "integer": DataType.NUMBER,
        "number": DataType.NUMBER,
        "boolean": DataType.BOOLEAN,
        "bool": DataType.BOOLEAN,
        "object": DataType.OBJECT,
        "array": DataType.ARRAY,
        "null": DataType.NULL,
        # Swagger 2.0 types
        "file": DataType.STRING,  # Treat file as string
    }

    # Parameter location mapping
    LOCATION_MAPPING = {
        "query": ParameterLocation.QUERY,
        "path": ParameterLocation.PATH,
        "header": ParameterLocation.HEADER,
        "body": ParameterLocation.BODY,
        "cookie": ParameterLocation.COOKIE,
        # Swagger 2.0 locations
        "formData": ParameterLocation.BODY,
    }

    def normalize_openapi(self, spec: Dict[str, Any]) -> List[CanonicalEndpoint]:
        """
        Normalize an entire OpenAPI/Swagger specification.

        Args:
            spec: OpenAPI spec dictionary (from OpenAPILoader)

        Returns:
            List of normalized CanonicalEndpoint objects

        Example:
            >>> spec = {"paths": {"/users": {"get": {...}}}}
            >>> endpoints = normalizer.normalize_openapi(spec)
        """
        endpoints = []

        paths = spec.get("paths", {})
        if not isinstance(paths, dict):
            return endpoints

        # Extract base path/servers for context
        base_info = self._extract_base_info(spec)

        # Process each path
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            # Process each HTTP method
            for method in ["get", "post", "put", "delete", "patch", "head", "options"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                if not isinstance(operation, dict):
                    continue

                # Normalize this endpoint
                endpoint = self._normalize_openapi_operation(
                    method=method,
                    path=path,
                    operation=operation,
                    base_info=base_info,
                )

                endpoints.append(endpoint)

        return endpoints

    def _extract_base_info(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract base information from OpenAPI spec (servers, basePath, etc.)."""
        base_info = {}

        # OpenAPI 3.x servers
        if "servers" in spec:
            servers = spec["servers"]
            if isinstance(servers, list) and servers:
                base_info["base_url"] = servers[0].get("url", "")

        # Swagger 2.x basePath
        if "basePath" in spec:
            base_info["base_path"] = spec["basePath"]

        # API info
        if "info" in spec:
            info = spec["info"]
            base_info["title"] = info.get("title", "Unknown API")
            base_info["version"] = info.get("version", "1.0.0")

        return base_info

    def _normalize_openapi_operation(
        self,
        method: str,
        path: str,
        operation: Dict[str, Any],
        base_info: Dict[str, Any],
    ) -> CanonicalEndpoint:
        """
        Normalize a single OpenAPI operation (path + method).

        Args:
            method: HTTP method (get, post, etc.)
            path: URL path
            operation: OpenAPI operation object
            base_info: Base API information

        Returns:
            CanonicalEndpoint instance
        """
        # Generate endpoint name
        name = self._generate_endpoint_name(operation, method, path)

        # Extract description and summary
        description = operation.get("description", "")
        summary = operation.get("summary", "")

        # Normalize parameters
        parameters = self._normalize_openapi_parameters(operation.get("parameters", []))

        # Extract request body schema (OpenAPI 3.x)
        body_schema = None
        if "requestBody" in operation:
            body_schema = self._normalize_openapi_schema(
                operation["requestBody"].get("content", {})
            )

        # Extract response schema
        response_schema = None
        responses = operation.get("responses", {})
        # Try to get successful response (200, 201, etc.)
        for status_code in ["200", "201", "default"]:
            if status_code in responses:
                response_obj = responses[status_code]
                if "content" in response_obj:
                    response_schema = self._normalize_openapi_schema(
                        response_obj["content"]
                    )
                    break
                # Swagger 2.0 uses 'schema' directly
                elif "schema" in response_obj:
                    response_schema = self._normalize_schema(response_obj["schema"])
                    break

        # Extract tags
        tags = operation.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        # Check if deprecated
        deprecated = operation.get("deprecated", False)

        return CanonicalEndpoint(
            name=name,
            method=method.upper(),
            path=path,
            description=description or summary or None,
            summary=summary or None,
            parameters=parameters,
            body_schema=body_schema,
            response_schema=response_schema,
            tags=tags,
            deprecated=deprecated,
        )

    def _generate_endpoint_name(
        self,
        operation: Dict[str, Any],
        method: str,
        path: str,
    ) -> str:
        """
        Generate a snake_case name for the endpoint.

        Priority:
        1. operationId (if present)
        2. Generated from method + path

        Args:
            operation: OpenAPI operation object
            method: HTTP method
            path: URL path

        Returns:
            snake_case endpoint name
        """
        # Use operationId if available
        if "operationId" in operation:
            return self._to_snake_case(operation["operationId"])

        # Generate from method + path
        # Example: GET /users/{id} -> get_users_by_id
        path_parts = [p for p in path.split("/") if p and not p.startswith("{")]
        name_parts = [method] + path_parts

        # Handle path parameters
        param_match = re.findall(r"\{(\w+)\}", path)
        if param_match:
            name_parts.append("by")
            name_parts.extend(param_match)

        name = "_".join(name_parts)
        return self._to_snake_case(name)

    def _normalize_openapi_parameters(
        self,
        parameters: List[Dict[str, Any]],
    ) -> List[CanonicalParameter]:
        """
        Normalize OpenAPI parameters array.

        Args:
            parameters: List of OpenAPI parameter objects

        Returns:
            List of CanonicalParameter instances
        """
        normalized = []

        for param in parameters:
            if not isinstance(param, dict):
                continue

            # Extract parameter info
            name = param.get("name", "")
            location = param.get("in", "query")
            required = param.get("required", False)
            description = param.get("description", "")

            # Validate parameter name
            if not name or not name.strip():
                logger.warning(
                    f"Skipping parameter with empty name. Location: {location}, "
                    f"Description: {description[:50] if description else 'N/A'}"
                )
                continue

            # Normalize the name and validate it's not empty after normalization
            normalized_name = self._to_snake_case(name)
            if not normalized_name:
                logger.warning(
                    f"Skipping parameter '{name}' - name became empty after normalization. "
                    f"Location: {location}"
                )
                continue

            # Extract type from schema (OpenAPI 3.x) or directly (Swagger 2.x)
            param_type = DataType.STRING  # Default
            default_value = None
            example_value = None

            if "schema" in param:
                schema = param["schema"]
                param_type = self._normalize_type(schema.get("type", "string"))
                default_value = schema.get("default")
                example_value = schema.get("example")
            elif "type" in param:
                # Swagger 2.0 style
                param_type = self._normalize_type(param["type"])
                default_value = param.get("default")
                example_value = param.get("example")

            # Normalize location
            normalized_location = self.LOCATION_MAPPING.get(
                location, ParameterLocation.QUERY
            )

            # Create parameter (wrap in try-catch for additional safety)
            try:
                normalized.append(
                    CanonicalParameter(
                        name=normalized_name,
                        location=normalized_location,
                        type=param_type,
                        required=required,
                        description=description or None,
                        default=default_value,
                        example=example_value,
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Skipping invalid parameter '{name}' (normalized: '{normalized_name}'): {e}"
                )

        return normalized

    def _normalize_openapi_schema(
        self,
        content: Dict[str, Any],
    ) -> Optional[CanonicalSchema]:
        """
        Normalize OpenAPI content/media type object to schema.

        Handles: application/json, application/xml, etc.

        Args:
            content: OpenAPI content object (mediaType dict)

        Returns:
            CanonicalSchema or None
        """
        # Try application/json first
        for media_type in ["application/json", "application/xml", "*/*"]:
            if media_type in content:
                media_obj = content[media_type]
                if "schema" in media_obj:
                    return self._normalize_schema(media_obj["schema"])

        return None

    def _normalize_schema(self, schema: Dict[str, Any]) -> CanonicalSchema:
        """
        Normalize a JSON Schema to CanonicalSchema.

        Args:
            schema: JSON Schema object

        Returns:
            CanonicalSchema instance
        """
        schema_type = self._normalize_type(schema.get("type", "object"))

        # Handle properties (for object types)
        properties = None
        if "properties" in schema:
            properties = {
                self._to_snake_case(key): self._normalize_schema(value)
                for key, value in schema["properties"].items()
            }

        # Handle items (for array types)
        items = None
        if "items" in schema:
            items = self._normalize_schema(schema["items"])

        # Required fields
        required = schema.get("required", [])

        # Description and example
        description = schema.get("description")
        example = schema.get("example")

        return CanonicalSchema(
            type=schema_type,
            properties=properties,
            items=items,
            required=required,
            description=description,
            example=example,
        )

    def _normalize_type(self, type_str: Any) -> DataType:
        """
        Normalize a type string to DataType enum.

        Args:
            type_str: Type string from source format

        Returns:
            DataType enum value
        """
        if not isinstance(type_str, str):
            return DataType.STRING

        type_lower = type_str.lower().strip()
        return self.TYPE_MAPPING.get(type_lower, DataType.STRING)

    def _to_snake_case(self, text: str) -> str:
        """
        Convert text to snake_case.

        Handles:
        - camelCase -> snake_case
        - PascalCase -> snake_case
        - kebab-case -> snake_case
        - Spaces -> underscores

        Args:
            text: Input string

        Returns:
            snake_case string
        """
        if not text:
            return ""

        # Replace hyphens and spaces with underscores
        text = text.replace("-", "_").replace(" ", "_")

        # Insert underscore before uppercase letters (camelCase/PascalCase)
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)

        # Convert to lowercase
        text = text.lower()

        # Remove multiple consecutive underscores
        text = re.sub(r"_+", "_", text)

        # Remove leading/trailing underscores
        text = text.strip("_")

        return text
