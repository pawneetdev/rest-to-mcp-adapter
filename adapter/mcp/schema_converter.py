"""
JSON Schema converter for MCP tool parameters.

Converts canonical data models (CanonicalSchema, CanonicalParameter) to
JSON Schema format required by the Model Context Protocol.

JSON Schema is the standard format for describing the structure and
validation rules of JSON data, and MCP uses it for tool input schemas.
"""

from typing import Any, Dict, List, Optional

from ..parsing.canonical_models import (
    CanonicalParameter,
    CanonicalSchema,
    DataType,
    ParameterLocation,
)


class SchemaConverter:
    """
    Converts canonical models to JSON Schema format.

    JSON Schema is used by MCP to define the expected input structure
    for tools. This converter transforms our internal canonical format
    into the JSON Schema format that MCP expects.

    Examples:
        >>> converter = SchemaConverter()
        >>> parameters = [
        ...     CanonicalParameter(
        ...         name="user_id",
        ...         location="path",
        ...         type="string",
        ...         required=True,
        ...         description="User identifier"
        ...     )
        ... ]
        >>> schema = converter.parameters_to_json_schema(parameters)
        >>> print(schema)
        {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                }
            },
            "required": ["user_id"]
        }
    """

    # Map our canonical types to JSON Schema types
    TYPE_MAPPING = {
        DataType.STRING: "string",
        DataType.NUMBER: "number",
        DataType.BOOLEAN: "boolean",
        DataType.OBJECT: "object",
        DataType.ARRAY: "array",
        DataType.NULL: "null",
    }

    def parameters_to_json_schema(
        self,
        parameters: List[CanonicalParameter],
        group_by_location: bool = False,
    ) -> Dict[str, Any]:
        """
        Convert a list of parameters to JSON Schema.

        Args:
            parameters: List of canonical parameters
            group_by_location: If True, group parameters by location
                             (path, query, header, body)

        Returns:
            JSON Schema object describing the parameters

        Examples:
            >>> converter = SchemaConverter()
            >>> params = [CanonicalParameter(...)]
            >>> schema = converter.parameters_to_json_schema(params)
        """
        if group_by_location:
            return self._parameters_grouped_schema(parameters)
        else:
            return self._parameters_flat_schema(parameters)

    def _parameters_flat_schema(
        self,
        parameters: List[CanonicalParameter],
    ) -> Dict[str, Any]:
        """
        Create a flat JSON Schema from parameters.

        All parameters are at the same level in the schema.
        """
        properties = {}
        required = []

        for param in parameters:
            # Convert parameter to JSON Schema property
            prop_schema = self._parameter_to_property(param)
            properties[param.name] = prop_schema

            # Track required parameters
            if param.required:
                required.append(param.name)

        schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        return schema

    def _parameters_grouped_schema(
        self,
        parameters: List[CanonicalParameter],
    ) -> Dict[str, Any]:
        """
        Create a grouped JSON Schema from parameters.

        Parameters are grouped by location (path, query, header, body).
        """
        grouped = {
            "path": [],
            "query": [],
            "header": [],
            "body": [],
        }

        # Group parameters by location
        for param in parameters:
            location = param.location.value if hasattr(param.location, 'value') else param.location
            if location in grouped:
                grouped[location].append(param)

        # Build schema with nested structure
        properties = {}
        required = []

        for location, params in grouped.items():
            if not params:
                continue

            location_schema = self._parameters_flat_schema(params)
            properties[location] = location_schema

            # If any parameters in this location are required, mark location as required
            if location_schema.get("required"):
                required.append(location)

        schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        return schema

    def _parameter_to_property(
        self,
        parameter: CanonicalParameter,
    ) -> Dict[str, Any]:
        """
        Convert a single parameter to a JSON Schema property.

        Args:
            parameter: Canonical parameter

        Returns:
            JSON Schema property definition
        """
        # Get JSON Schema type
        param_type = parameter.type
        if isinstance(param_type, DataType):
            json_type = self.TYPE_MAPPING.get(param_type, "string")
        else:
            json_type = str(param_type)

        # Build property schema
        prop = {
            "type": json_type,
        }

        # Add description if available
        if parameter.description:
            prop["description"] = parameter.description

        # Add default value if available
        if parameter.default is not None:
            prop["default"] = parameter.default

        # Add example if available
        if parameter.example is not None:
            prop["example"] = parameter.example

        return prop

    def canonical_schema_to_json_schema(
        self,
        schema: CanonicalSchema,
    ) -> Dict[str, Any]:
        """
        Convert a CanonicalSchema to JSON Schema.

        This handles complex schemas including nested objects and arrays.

        Args:
            schema: Canonical schema

        Returns:
            JSON Schema representation
        """
        # Get base type
        schema_type = schema.type
        if isinstance(schema_type, DataType):
            json_type = self.TYPE_MAPPING.get(schema_type, "string")
        else:
            json_type = str(schema_type)

        json_schema = {
            "type": json_type,
        }

        # Add description if available
        if schema.description:
            json_schema["description"] = schema.description

        # Handle object type with properties
        if json_type == "object" and schema.properties:
            properties = {}
            for prop_name, prop_schema in schema.properties.items():
                properties[prop_name] = self.canonical_schema_to_json_schema(prop_schema)
            json_schema["properties"] = properties

            # Add required fields
            if schema.required:
                json_schema["required"] = schema.required

        # Handle array type with items
        if json_type == "array" and schema.items:
            json_schema["items"] = self.canonical_schema_to_json_schema(schema.items)

        # Add example if available
        if schema.example is not None:
            json_schema["example"] = schema.example

        return json_schema
