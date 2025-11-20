"""
OpenAPI/Swagger specification loader with URL and file path support.

This loader handles:
- OpenAPI 3.x specifications
- Swagger 2.x specifications
- Both JSON and YAML formats
- Loading from URLs, file paths, or raw content
- Partial/malformed specs (with graceful degradation)

The loader leverages LangChain's OpenAPISpec utility for parsing and validation
when available, with a fallback to manual parsing for flexibility.

Design notes:
- Supports URLs, file paths, and raw content
- Prefers LangChain utilities for standardization
- Resilient to missing or malformed fields
- Returns structured dict ready for normalization
"""

import json
from pathlib import Path
from typing import Any, Dict, Union
from urllib.parse import urlparse

import yaml

from .base_loader import BaseLoader, InvalidFormatError, ValidationError


class OpenAPILoader(BaseLoader):
    """
    Loader for OpenAPI and Swagger specifications.

    This loader can parse both OpenAPI 3.x and Swagger 2.x specifications
    in JSON or YAML format. It supports loading from:
    - URLs (http/https)
    - File paths (local filesystem)
    - Raw content strings

    It uses LangChain's OpenAPISpec when available for robust parsing,
    but can also handle specs manually.

    The loader is designed to be resilient:
    - Handles partial specs
    - Provides sensible defaults for missing fields
    - Validates required fields while being lenient with optional ones

    Examples:
        >>> # Load from URL
        >>> loader = OpenAPILoader()
        >>> spec = loader.load_from_url("https://api.example.com/openapi.json")
        >>> print(spec.keys())
        dict_keys(['openapi', 'info', 'paths', ...])

        >>> # Load from file path
        >>> spec = loader.load_from_file("./specs/api.yaml")

        >>> # Load from raw content
        >>> spec = loader.load(openapi_yaml_content)

        >>> # With strict validation
        >>> loader = OpenAPILoader(strict=True)
        >>> spec = loader.load(malformed_spec)  # Raises ValidationError
    """

    def __init__(self, strict: bool = False, use_langchain: bool = True):
        """
        Initialize the OpenAPI loader.

        Args:
            strict: If True, enforce strict validation (default: False)
            use_langchain: If True, prefer LangChain utilities (default: True)
        """
        self.strict = strict
        self.use_langchain = use_langchain

    def load_from_url(self, url: str) -> Dict[str, Any]:
        """
        Load OpenAPI spec from a URL.

        Args:
            url: URL to the OpenAPI specification (JSON or YAML)

        Returns:
            Parsed specification as a dictionary

        Raises:
            InvalidFormatError: If URL is invalid or content cannot be fetched
            ValueError: If URL scheme is not http/https

        Examples:
            >>> loader = OpenAPILoader()
            >>> spec = loader.load_from_url("https://api.example.com/openapi.json")
        """
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme in ["http", "https"]:
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Use http or https.")

        if not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")

        # Fetch content
        try:
            import requests

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

        except ImportError:
            raise InvalidFormatError(
                "requests library not available. Install with: uv add requests"
            )
        except requests.RequestException as e:
            raise InvalidFormatError(f"Failed to fetch URL {url}: {e}")

        # Parse and return
        return self.load(content)

    def load_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load OpenAPI spec from a file path.

        Args:
            file_path: Path to the OpenAPI specification file

        Returns:
            Parsed specification as a dictionary

        Raises:
            InvalidFormatError: If file cannot be read
            FileNotFoundError: If file does not exist

        Examples:
            >>> loader = OpenAPILoader()
            >>> spec = loader.load_from_file("./api/openapi.yaml")
            >>> spec = loader.load_from_file(Path("specs/api.json"))
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise InvalidFormatError(f"Not a file: {file_path}")

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise InvalidFormatError(f"Failed to read file {file_path}: {e}")

        # Parse and return
        return self.load(content)

    def load(self, content: str) -> Dict[str, Any]:
        """
        Load and parse OpenAPI/Swagger specification from raw content.

        This method intelligently detects if the content is:
        - A URL (starts with http:// or https://)
        - A file path (exists on filesystem)
        - Raw JSON/YAML content

        Args:
            content: OpenAPI spec as JSON/YAML string, URL, or file path

        Returns:
            Parsed specification as a dictionary

        Raises:
            InvalidFormatError: If content is not valid OpenAPI/Swagger
            ValidationError: If strict=True and spec is malformed

        Examples:
            >>> loader = OpenAPILoader()
            >>> # From URL
            >>> spec = loader.load("https://api.example.com/openapi.json")
            >>> # From file path
            >>> spec = loader.load("./specs/api.yaml")
            >>> # From raw content
            >>> spec = loader.load('{"openapi": "3.0.0", ...}')
        """
        if not content or not content.strip():
            raise InvalidFormatError("Content cannot be empty")

        content_stripped = content.strip()

        # Check if it's a URL (do this first, before file path check)
        if content_stripped.startswith(("http://", "https://")):
            return self.load_from_url(content_stripped)

        # Check if it's a file path (only for reasonable length strings)
        # Avoid "File name too long" errors for very long strings
        if len(content_stripped) < 4096:  # Max path length on most systems
            try:
                file_path = Path(content_stripped)
                if file_path.exists() and file_path.is_file():
                    return self.load_from_file(file_path)
            except (OSError, ValueError):
                # Not a valid file path, continue to treat as raw content
                pass

        # Otherwise, treat as raw content
        return self._load_from_content(content)

    def _load_from_content(self, content: str) -> Dict[str, Any]:
        """
        Internal method to load from raw content string.

        Args:
            content: Raw OpenAPI spec as JSON or YAML string

        Returns:
            Parsed specification as a dictionary

        Raises:
            InvalidFormatError: If content is not valid OpenAPI/Swagger
            ValidationError: If strict=True and spec is malformed
        """
        if not self.validate(content):
            raise InvalidFormatError("Content appears to be empty or invalid")

        # Parse the content (JSON or YAML)
        spec_dict = self._parse_content(content)

        # Try LangChain integration first if enabled
        if self.use_langchain:
            try:
                spec_dict = self._load_with_langchain(spec_dict)
            except ImportError:
                # LangChain not available, fall back to manual parsing
                pass
            except Exception as e:
                # LangChain failed, fall back to manual parsing
                if self.strict:
                    raise ValidationError(f"LangChain validation failed: {e}")

        # Dereference $ref pointers
        spec_dict = self._dereference_spec(spec_dict)

        # Validate the spec structure
        self._validate_spec(spec_dict)

        return spec_dict

    def _parse_content(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON or YAML content into a dictionary.

        Args:
            content: Raw content string

        Returns:
            Parsed dictionary

        Raises:
            InvalidFormatError: If content cannot be parsed
        """
        content_stripped = content.strip()

        # Try JSON first (faster)
        if content_stripped.startswith("{"):
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise InvalidFormatError(f"Invalid JSON: {e}")

        # Try YAML
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                raise InvalidFormatError(
                    f"Expected dict, got {type(data).__name__}"
                )
            return data
        except yaml.YAMLError as e:
            raise InvalidFormatError(f"Invalid YAML: {e}")

    def _load_with_langchain(self, spec_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load spec using LangChain's OpenAPISpec utility.

        This provides additional validation and normalization.

        Args:
            spec_dict: Parsed OpenAPI spec

        Returns:
            Validated and normalized spec dictionary

        Raises:
            ImportError: If LangChain is not installed
        """
        try:
            from langchain_community.utilities.openapi import OpenAPISpec

            # Create OpenAPISpec instance from dict
            # Note: OpenAPISpec expects the spec as a dict
            openapi_spec = OpenAPISpec.from_spec_dict(spec_dict)

            # Return the underlying spec dict
            # OpenAPISpec provides validation and normalization
            return openapi_spec.spec_dict

        except ImportError:
            raise ImportError(
                "LangChain not available. Install with: "
                "uv add langchain-community"
            )

    def _dereference_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dereference all $ref pointers in the OpenAPI spec.

        This method recursively walks through the spec and replaces all
        {'$ref': '...'} references with the actual definitions from components.

        Args:
            spec: OpenAPI spec dictionary

        Returns:
            Spec with all $ref pointers resolved

        Examples:
            >>> # Before: {'$ref': '#/components/parameters/timestamp'}
            >>> # After: {'name': 'timestamp', 'in': 'query', 'type': 'integer', ...}
        """
        # Track visited references to detect circular references
        visited = set()

        def resolve_ref(ref_path: str, root: Dict[str, Any]) -> Any:
            """
            Resolve a JSON Pointer reference like '#/components/parameters/timestamp'.

            Args:
                ref_path: The $ref path to resolve
                root: The root spec document

            Returns:
                The resolved definition

            Raises:
                ValueError: If reference cannot be resolved
            """
            # Check for circular reference
            if ref_path in visited:
                raise ValueError(f"Circular reference detected: {ref_path}")

            visited.add(ref_path)

            # Only handle internal references (starting with #/)
            if not ref_path.startswith("#/"):
                # External references not supported yet
                return {"$ref": ref_path}

            # Parse the path (e.g., "#/components/parameters/timestamp")
            # Remove the leading '#/'
            path_parts = ref_path[2:].split("/")

            # Navigate through the spec to find the definition
            current = root
            for part in path_parts:
                # Handle escaped characters in JSON Pointer
                part = part.replace("~1", "/").replace("~0", "~")

                if isinstance(current, dict):
                    if part not in current:
                        raise ValueError(f"Reference not found: {ref_path} (missing key: {part})")
                    current = current[part]
                elif isinstance(current, list):
                    try:
                        index = int(part)
                        current = current[index]
                    except (ValueError, IndexError):
                        raise ValueError(f"Invalid array reference: {ref_path} (index: {part})")
                else:
                    raise ValueError(f"Cannot navigate through {type(current)} at {ref_path}")

            # Recursively dereference the resolved definition
            resolved = dereference_value(current, root)

            visited.remove(ref_path)
            return resolved

        def dereference_value(value: Any, root: Dict[str, Any]) -> Any:
            """
            Recursively dereference a value.

            Args:
                value: The value to dereference (can be dict, list, or primitive)
                root: The root spec document

            Returns:
                The dereferenced value
            """
            if isinstance(value, dict):
                # Check if this is a $ref object
                if "$ref" in value and len(value) == 1:
                    # This is a pure reference, resolve it
                    return resolve_ref(value["$ref"], root)
                elif "$ref" in value:
                    # This is a reference with additional properties (allOf pattern)
                    # Resolve the reference and merge with other properties
                    ref_resolved = resolve_ref(value["$ref"], root)
                    result = {}

                    # Start with resolved reference
                    if isinstance(ref_resolved, dict):
                        result.update(ref_resolved)

                    # Override with local properties (excluding $ref)
                    for key, val in value.items():
                        if key != "$ref":
                            result[key] = dereference_value(val, root)

                    return result
                else:
                    # Regular dict, recursively dereference all values
                    return {key: dereference_value(val, root) for key, val in value.items()}

            elif isinstance(value, list):
                # Recursively dereference all items
                return [dereference_value(item, root) for item in value]

            else:
                # Primitive value, return as-is
                return value

        # Start dereferencing from the root
        try:
            return dereference_value(spec, spec)
        except Exception as e:
            # If dereferencing fails and we're in strict mode, raise
            if self.strict:
                raise ValidationError(f"Failed to dereference spec: {e}")
            # Otherwise, return original spec with a warning
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to dereference spec: {e}. Continuing with partial dereferencing.")
            return spec

    def _validate_spec(self, spec_dict: Dict[str, Any]) -> None:
        """
        Validate OpenAPI/Swagger spec structure.

        Checks for required fields based on OpenAPI 3.x and Swagger 2.x specs.

        Args:
            spec_dict: Parsed spec dictionary

        Raises:
            ValidationError: If required fields are missing (in strict mode)
        """
        if not isinstance(spec_dict, dict):
            raise ValidationError("Spec must be a dictionary")

        # Check for version field
        has_openapi = "openapi" in spec_dict
        has_swagger = "swagger" in spec_dict

        if not has_openapi and not has_swagger:
            if self.strict:
                raise ValidationError(
                    "Spec must contain 'openapi' or 'swagger' version field"
                )

        # Check for required fields
        required_fields = ["info"]  # 'info' is required in both OpenAPI and Swagger

        # 'paths' is technically required, but we allow it to be missing
        # for partial/incomplete specs (common in documentation)
        if self.strict and "paths" not in spec_dict:
            raise ValidationError("Spec must contain 'paths' field")

        for field in required_fields:
            if field not in spec_dict:
                if self.strict:
                    raise ValidationError(f"Missing required field: {field}")
                else:
                    # Provide default for missing fields
                    if field == "info":
                        spec_dict["info"] = {"title": "Unknown API", "version": "1.0.0"}

        # Validate info field structure
        if "info" in spec_dict:
            info = spec_dict["info"]
            if not isinstance(info, dict):
                raise ValidationError("'info' field must be a dictionary")

            if self.strict:
                if "title" not in info:
                    raise ValidationError("'info' must contain 'title'")
                if "version" not in info:
                    raise ValidationError("'info' must contain 'version'")

    def extract_auth_parameters(self, spec_dict: Dict[str, Any]) -> set:
        """
        Extract authentication parameter names from OpenAPI security schemes.

        This method parses the securitySchemes section of an OpenAPI spec and
        identifies parameter names that are used for authentication. These
        parameters should typically be excluded from user-facing tool schemas
        since they are managed by authentication handlers.

        Supports:
        - OpenAPI 3.x: components.securitySchemes
        - Swagger 2.x: securityDefinitions

        Args:
            spec_dict: Parsed OpenAPI/Swagger spec dictionary

        Returns:
            Set of lowercase parameter names used for authentication

        Examples:
            >>> loader = OpenAPILoader()
            >>> spec = loader.load("api.yaml")
            >>> auth_params = loader.extract_auth_parameters(spec)
            >>> print(auth_params)
            {'signature', 'timestamp', 'api_key', 'authorization'}
        """
        auth_params = set()

        # OpenAPI 3.x: components.securitySchemes
        if "components" in spec_dict and "securitySchemes" in spec_dict["components"]:
            security_schemes = spec_dict["components"]["securitySchemes"]
            auth_params.update(self._extract_from_security_schemes(security_schemes))

        # Swagger 2.x: securityDefinitions
        elif "securityDefinitions" in spec_dict:
            security_schemes = spec_dict["securityDefinitions"]
            auth_params.update(self._extract_from_security_schemes(security_schemes))

        return auth_params

    def _extract_from_security_schemes(self, security_schemes: Dict[str, Any]) -> set:
        """
        Extract parameter names from security scheme definitions.

        Args:
            security_schemes: Security schemes dictionary from OpenAPI spec

        Returns:
            Set of lowercase parameter names
        """
        auth_params = set()

        if not isinstance(security_schemes, dict):
            return auth_params

        for scheme_name, scheme_def in security_schemes.items():
            if not isinstance(scheme_def, dict):
                continue

            scheme_type = scheme_def.get("type", "").lower()

            # apiKey type - has explicit parameter name
            if scheme_type == "apikey":
                param_name = scheme_def.get("name", "")
                if param_name:
                    auth_params.add(param_name.lower())

            # http type - typically Authorization header or similar
            elif scheme_type == "http":
                scheme = scheme_def.get("scheme", "").lower()
                # Bearer tokens use Authorization header
                if scheme in ("bearer", "basic", "digest"):
                    auth_params.add("authorization")

            # oauth2 type - often uses access_token parameter or Authorization header
            elif scheme_type == "oauth2":
                auth_params.add("authorization")
                auth_params.add("access_token")
                auth_params.add("token")

            # openIdConnect - uses Authorization header
            elif scheme_type == "openidconnect":
                auth_params.add("authorization")

        return auth_params

    def validate(self, content: str) -> bool:
        """
        Pre-flight validation of content.

        Args:
            content: Raw content string

        Returns:
            True if content appears to be valid OpenAPI/Swagger
        """
        if not content or not content.strip():
            return False

        try:
            spec_dict = self._parse_content(content)

            # Quick check for OpenAPI/Swagger markers
            if "openapi" in spec_dict or "swagger" in spec_dict:
                return True

            # Also accept if it has 'paths' (might be partial spec)
            if "paths" in spec_dict:
                return True

        except (InvalidFormatError, Exception):
            return False

        return False
