"""
HTML documentation loader with URL and LangChain support.

This loader handles HTML-based API documentation (e.g., CoinDCX-style docs).
It can load from URLs or raw HTML content, cleans and extracts text,
preparing it for LLM-based parsing in future phases.

Features:
- Load from URL or raw HTML content
- Remove scripts, styles, navigation, and boilerplate
- Extract clean, readable text
- Preserve structure hints (headings, lists, etc.)
- Use LangChain's BSHTMLLoader when available

Future Enhancement:
- Recursive crawling: The loader could be extended to recursively crawl
  linked documentation pages to discover all API endpoints across multiple pages.
  This would involve following internal links, deduplicating URLs, and
  aggregating content from the entire documentation site.
"""

import re
from typing import Optional
from urllib.parse import urlparse

from .base_loader import BaseLoader, InvalidFormatError


class HTMLLoader(BaseLoader):
    """
    Loader for HTML-based API documentation.

    This loader extracts clean text from HTML documentation pages,
    removing scripts, styles, navigation, and other boilerplate content.
    It supports loading from URLs or raw HTML strings.

    The goal is to produce clean, structured text that can be processed
    by LLMs in later phases to extract endpoint information.

    Features:
    - Load from URL or raw HTML content
    - Uses LangChain's BSHTMLLoader when available
    - Falls back to BeautifulSoup for manual cleaning
    - Configurable filtering of HTML elements
    - Preserves document structure (headings, lists, etc.)

    Examples:
        >>> # Load from URL
        >>> loader = HTMLLoader()
        >>> text = loader.load_from_url("https://api-docs.example.com")
        >>> print(text)  # Clean text without HTML tags

        >>> # Load from raw HTML
        >>> text = loader.load(html_content)

        >>> # With custom filtering
        >>> loader = HTMLLoader(remove_tags=['nav', 'footer', 'aside'])
        >>> text = loader.load(html_content)

    Future: Recursive Crawling
        The loader can be extended to support recursive crawling:
        >>> loader = HTMLLoader(recursive=True, max_depth=3)
        >>> all_content = loader.load_from_url("https://docs.api.com")
        # Would crawl all linked pages and aggregate content
    """

    # Default tags to remove (boilerplate/noise)
    DEFAULT_REMOVE_TAGS = [
        "script",
        "style",
        "nav",
        "header",
        "footer",
        "aside",
        "iframe",
        "noscript",
    ]

    # Default attributes to remove elements by
    DEFAULT_REMOVE_CLASSES = [
        "advertisement",
        "ads",
        "banner",
        "cookie-notice",
        "popup",
        "modal",
    ]

    def __init__(
        self,
        use_langchain: bool = True,
        remove_tags: Optional[list] = None,
        remove_classes: Optional[list] = None,
        preserve_structure: bool = True,
    ):
        """
        Initialize the HTML loader.

        Args:
            use_langchain: Prefer LangChain's BSHTMLLoader if available
            remove_tags: HTML tags to remove (default: nav, scripts, etc.)
            remove_classes: CSS classes to filter out (default: ads, etc.)
            preserve_structure: Keep headings and list structure markers
        """
        self.use_langchain = use_langchain
        self.remove_tags = remove_tags or self.DEFAULT_REMOVE_TAGS
        self.remove_classes = remove_classes or self.DEFAULT_REMOVE_CLASSES
        self.preserve_structure = preserve_structure

    def load_from_url(self, url: str) -> str:
        """
        Load and clean HTML content from a URL.

        Args:
            url: URL of the HTML documentation page

        Returns:
            Clean text extracted from HTML

        Raises:
            InvalidFormatError: If URL is invalid or content cannot be fetched
            ValueError: If URL scheme is not http/https

        Examples:
            >>> loader = HTMLLoader()
            >>> text = loader.load_from_url("https://docs.example.com/api")
        """
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme in ["http", "https"]:
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Use http or https.")

        if not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")

        # Fetch HTML content
        try:
            import requests

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            html_content = response.text

        except ImportError:
            raise InvalidFormatError(
                "requests library not available. Install with: uv add requests"
            )
        except requests.RequestException as e:
            raise InvalidFormatError(f"Failed to fetch URL {url}: {e}")

        # Process the HTML content
        return self.load(html_content)

    def load(self, content: str) -> str:
        """
        Load and clean HTML content from a string.

        Args:
            content: Raw HTML string or URL

        Returns:
            Clean text extracted from HTML

        Raises:
            InvalidFormatError: If content is not valid HTML

        Examples:
            >>> loader = HTMLLoader()
            >>> text = loader.load("<html><body>API Docs</body></html>")
        """
        if not content or not content.strip():
            raise InvalidFormatError("Content cannot be empty")

        # Check if content looks like a URL
        if content.strip().startswith(("http://", "https://")):
            return self.load_from_url(content.strip())

        if not self.validate(content):
            raise InvalidFormatError("Content does not appear to be valid HTML")

        # Try LangChain integration first if enabled
        if self.use_langchain:
            try:
                return self._load_with_langchain(content)
            except ImportError:
                # LangChain not available, fall back to manual parsing
                pass
            except Exception:
                # LangChain failed, fall back to manual parsing
                pass

        # Manual HTML cleaning with BeautifulSoup
        return self._load_with_beautifulsoup(content)

    def _load_with_langchain(self, content: str) -> str:
        """
        Load HTML using LangChain's BSHTMLLoader.

        Note: BSHTMLLoader typically expects a file path, so we need to
        work with the Document objects it returns.

        Args:
            content: HTML content string

        Returns:
            Cleaned text content

        Raises:
            ImportError: If LangChain is not available
        """
        try:
            from langchain_community.document_loaders import BSHTMLLoader
            import tempfile
            import os

            # BSHTMLLoader expects a file path, so create a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".html",
                delete=False,
                encoding="utf-8"
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                # Load with BSHTMLLoader
                loader = BSHTMLLoader(tmp_path)
                documents = loader.load()

                # Extract text from documents
                text_parts = [doc.page_content for doc in documents]
                combined_text = "\n\n".join(text_parts)

                return self._post_process_text(combined_text)

            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except ImportError:
            raise ImportError(
                "LangChain not available. Install with: "
                "uv add langchain-community beautifulsoup4"
            )

    def _load_with_beautifulsoup(self, content: str) -> str:
        """
        Load and clean HTML using BeautifulSoup directly.

        This is the fallback method when LangChain is not available.

        Args:
            content: HTML content string

        Returns:
            Cleaned text content

        Raises:
            InvalidFormatError: If BeautifulSoup is not available
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise InvalidFormatError(
                "BeautifulSoup not available. Install with: "
                "uv add beautifulsoup4"
            )

        # Parse HTML
        soup = BeautifulSoup(content, "html.parser")

        # Remove unwanted tags
        for tag_name in self.remove_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove elements with unwanted classes
        for class_name in self.remove_classes:
            for tag in soup.find_all(class_=class_name):
                tag.decompose()

        # Extract text with optional structure preservation
        if self.preserve_structure:
            text = self._extract_structured_text(soup)
        else:
            text = soup.get_text()

        return self._post_process_text(text)

    def _extract_structured_text(self, soup) -> str:
        """
        Extract text while preserving document structure.

        This adds markdown-like markers for headings and lists
        to help LLMs understand the document structure.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Text with structure markers
        """
        lines = []

        # Process each top-level element
        for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "pre", "code"]):
            tag_name = element.name

            # Add markers for headings
            if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                level = int(tag_name[1])
                heading_text = element.get_text().strip()
                if heading_text:
                    lines.append(f"\n{'#' * level} {heading_text}\n")

            # Add markers for lists
            elif tag_name in ["ul", "ol"]:
                for li in element.find_all("li", recursive=False):
                    li_text = li.get_text().strip()
                    if li_text:
                        lines.append(f"- {li_text}")

            # Code blocks
            elif tag_name in ["pre", "code"]:
                code_text = element.get_text().strip()
                if code_text:
                    lines.append(f"\n```\n{code_text}\n```\n")

            # Regular paragraphs
            elif tag_name == "p":
                p_text = element.get_text().strip()
                if p_text:
                    lines.append(p_text)

        return "\n".join(lines)

    def _post_process_text(self, text: str) -> str:
        """
        Clean up extracted text.

        Removes:
        - Excessive whitespace
        - Empty lines (more than 2 consecutive)
        - Leading/trailing whitespace

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Normalize whitespace
        text = re.sub(r"[ \t]+", " ", text)

        # Remove excessive blank lines (max 2 consecutive)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

        # Trim leading/trailing whitespace
        text = text.strip()

        return text

    def validate(self, content: str) -> bool:
        """
        Validate that content appears to be HTML.

        Args:
            content: Raw content string

        Returns:
            True if content looks like HTML
        """
        if not content or not content.strip():
            return False

        content_lower = content.lower().strip()

        # Check for HTML markers
        html_markers = [
            "<!doctype html",
            "<html",
            "<head",
            "<body",
        ]

        return any(marker in content_lower for marker in html_markers)
