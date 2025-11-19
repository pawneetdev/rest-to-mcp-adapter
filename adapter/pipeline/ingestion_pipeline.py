"""
End-to-end ingestion pipeline for API documentation.

This module provides the high-level orchestration layer that ties together:
- Format detection
- Content loading
- (Future: Normalization and parsing)

The pipeline is the main entry point for ingesting API documentation
and preparing it for MCP tool generation.

Usage:
    >>> from adapter.pipeline import ingest_api_source
    >>> result = ingest_api_source(
    ...     source="my_api.yaml",
    ...     raw_content=yaml_content
    ... )
    >>> print(result.format)  # APIFormat.OPENAPI
    >>> print(result.loaded_data)  # Parsed spec dict
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

from ..ingestion.detector import APIFormat, FormatDetector
from ..ingestion.base_loader import BaseLoader, LoaderError
from ..ingestion.loader_openapi import OpenAPILoader
from ..ingestion.loader_html import HTMLLoader


@dataclass
class IngestionResult:
    """
    Result of the ingestion pipeline.

    This data class encapsulates everything produced by the ingestion phase:
    - Detected format
    - Loaded data (structured dict or clean text)
    - Original source identifier
    - Success/error status
    - Metadata about the ingestion process

    Attributes:
        format: Detected APIFormat
        loaded_data: Parsed data (dict for structured formats, str for text)
        source: Original source identifier (filename or description)
        success: Whether ingestion succeeded
        error: Error message if ingestion failed
        metadata: Additional information about the ingestion
    """

    format: APIFormat
    loaded_data: Union[Dict[str, Any], str, None]
    source: str
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __repr__(self) -> str:
        """String representation."""
        status = "Success" if self.success else "Failed"
        data_type = type(self.loaded_data).__name__ if self.loaded_data else "None"
        return (
            f"IngestionResult(format={self.format}, "
            f"status={status}, "
            f"data_type={data_type}, "
            f"source={self.source})"
        )


class IngestionPipeline:
    """
    Orchestrates the complete ingestion process.

    This class coordinates:
    1. Format detection
    2. Loader selection
    3. Content loading
    4. Error handling and recovery

    The pipeline is designed to be extensible:
    - New formats can be added by registering loaders
    - Custom loaders can be injected
    - Configuration can be customized

    Examples:
        >>> pipeline = IngestionPipeline()
        >>> result = pipeline.ingest(
        ...     source="openapi.yaml",
        ...     content=yaml_content
        ... )

        >>> # With custom configuration
        >>> pipeline = IngestionPipeline(strict=True)
        >>> result = pipeline.ingest(source="spec.json", content=content)
    """

    def __init__(
        self,
        strict: bool = False,
        use_langchain: bool = True,
    ):
        """
        Initialize the ingestion pipeline.

        Args:
            strict: Enable strict validation (default: False)
            use_langchain: Prefer LangChain utilities when available (default: True)
        """
        self.strict = strict
        self.use_langchain = use_langchain

        # Initialize components
        self.detector = FormatDetector()

        # Loader registry: maps APIFormat -> Loader class
        self._loader_registry: Dict[APIFormat, type] = {
            APIFormat.OPENAPI: OpenAPILoader,
            APIFormat.HTML: HTMLLoader,
        }

    def ingest(
        self,
        source: str,
        content: str,
        format_hint: Optional[APIFormat] = None,
    ) -> IngestionResult:
        """
        Execute the complete ingestion pipeline.

        This is the main entry point for ingesting API documentation.

        Steps:
        1. Detect format (or use hint)
        2. Select appropriate loader
        3. Load and parse content
        4. Return structured result

        Args:
            source: Source identifier (filename or description)
            content: Raw documentation content
            format_hint: Optional format hint (bypasses detection)

        Returns:
            IngestionResult with loaded data and metadata

        Examples:
            >>> pipeline = IngestionPipeline()
            >>> result = pipeline.ingest("api.yaml", yaml_content)
            >>> if result.success:
            ...     print(result.loaded_data)
        """
        metadata = {"source": source}

        try:
            # Step 1: Format detection
            if format_hint:
                detected_format = format_hint
                metadata["format_hint"] = True
            else:
                detected_format = self.detector.detect(
                    content=content,
                    filename=source,
                )
                metadata["format_hint"] = False

            metadata["detected_format"] = detected_format.value

            # Step 2: Select loader
            loader = self._get_loader(detected_format)

            if loader is None:
                return IngestionResult(
                    format=detected_format,
                    loaded_data=None,
                    source=source,
                    success=False,
                    error=f"No loader available for format: {detected_format}",
                    metadata=metadata,
                )

            # Step 3: Load content
            loaded_data = loader.load(content)

            metadata["loader_type"] = loader.__class__.__name__

            return IngestionResult(
                format=detected_format,
                loaded_data=loaded_data,
                source=source,
                success=True,
                metadata=metadata,
            )

        except LoaderError as e:
            # Loader-specific error
            return IngestionResult(
                format=detected_format if 'detected_format' in locals() else APIFormat.UNKNOWN,
                loaded_data=None,
                source=source,
                success=False,
                error=f"Loader error: {str(e)}",
                metadata=metadata,
            )

        except Exception as e:
            # Unexpected error
            return IngestionResult(
                format=detected_format if 'detected_format' in locals() else APIFormat.UNKNOWN,
                loaded_data=None,
                source=source,
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=metadata,
            )

    def _get_loader(self, format: APIFormat) -> Optional[BaseLoader]:
        """
        Get appropriate loader for the detected format.

        Args:
            format: Detected APIFormat

        Returns:
            Instantiated loader or None if format not supported
        """
        loader_class = self._loader_registry.get(format)

        if loader_class is None:
            return None

        # Instantiate loader with pipeline configuration
        if format == APIFormat.OPENAPI:
            return loader_class(
                strict=self.strict,
                use_langchain=self.use_langchain,
            )
        elif format == APIFormat.HTML:
            return loader_class(
                use_langchain=self.use_langchain,
            )
        else:
            # Generic instantiation
            return loader_class()

    def register_loader(
        self,
        format: APIFormat,
        loader_class: type,
    ) -> None:
        """
        Register a custom loader for a format.

        This allows extending the pipeline with new loaders
        without modifying the core code.

        Args:
            format: APIFormat to register
            loader_class: Loader class (must extend BaseLoader)

        Example:
            >>> class MyCustomLoader(BaseLoader):
            ...     def load(self, content: str) -> dict:
            ...         return {"custom": "data"}
            ...
            >>> pipeline.register_loader(APIFormat.POSTMAN, MyCustomLoader)
        """
        if not issubclass(loader_class, BaseLoader):
            raise ValueError(f"{loader_class} must extend BaseLoader")

        self._loader_registry[format] = loader_class


# Convenience function for simple use cases
def ingest_api_source(
    source: str,
    raw_content: str,
    format_hint: Optional[str] = None,
    strict: bool = False,
    use_langchain: bool = True,
) -> IngestionResult:
    """
    Ingest API documentation (convenience function).

    This is a simplified interface to the ingestion pipeline
    for straightforward use cases.

    Args:
        source: Source identifier (filename or description)
        raw_content: Raw documentation content as string
        format_hint: Optional format hint ("openapi", "html", etc.)
        strict: Enable strict validation (default: False)
        use_langchain: Prefer LangChain utilities (default: True)

    Returns:
        IngestionResult with loaded data

    Examples:
        >>> # Ingest OpenAPI spec
        >>> result = ingest_api_source(
        ...     source="petstore.yaml",
        ...     raw_content=yaml_content
        ... )
        >>> if result.success:
        ...     endpoints = normalizer.normalize_openapi(result.loaded_data)

        >>> # Ingest HTML docs
        >>> result = ingest_api_source(
        ...     source="api_docs.html",
        ...     raw_content=html_content
        ... )
        >>> if result.success:
        ...     # Pass clean text to LLM for extraction (future phase)
        ...     clean_text = result.loaded_data

        >>> # With format hint
        >>> result = ingest_api_source(
        ...     source="unknown_file",
        ...     raw_content=content,
        ...     format_hint="openapi"
        ... )
    """
    # Convert format hint string to enum
    format_enum = None
    if format_hint:
        try:
            format_enum = APIFormat(format_hint.lower())
        except ValueError:
            pass  # Invalid hint, will be ignored

    # Create pipeline and ingest
    pipeline = IngestionPipeline(
        strict=strict,
        use_langchain=use_langchain,
    )

    return pipeline.ingest(
        source=source,
        content=raw_content,
        format_hint=format_enum,
    )
