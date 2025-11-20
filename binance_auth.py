"""
Custom authentication handler for Binance API.

Binance uses HMAC SHA256 signature authentication with:
- API Key in X-MBX-APIKEY header
- Secret for signing requests
- timestamp parameter
- signature parameter (HMAC SHA256 of query string)
"""

import hmac
import hashlib
import time
from typing import Dict
from urllib.parse import urlencode

from adapter.runtime.auth import AuthHandler, AuthType


class BinanceAuth(AuthHandler):
    """
    Binance API authentication handler.

    Implements Binance's signature-based authentication:
    1. Adds X-MBX-APIKEY header with the API key
    2. Adds timestamp parameter
    3. Generates HMAC SHA256 signature of the query string
    4. Adds signature parameter

    Examples:
        >>> auth = BinanceAuth(api_key="your_api_key", api_secret="your_secret")
        >>> headers = {}
        >>> params = {"symbol": "BTCUSDT"}
        >>> auth.apply(headers, params)
        >>> # headers now contains: {"X-MBX-APIKEY": "your_api_key"}
        >>> # params now contains: {"symbol": "BTCUSDT", "timestamp": ..., "signature": ...}
    """

    def __init__(self, api_key: str, api_secret: str, recv_window: int = 5000):
        """
        Initialize Binance authentication.

        Args:
            api_key: Your Binance API key
            api_secret: Your Binance API secret
            recv_window: Request validity window in milliseconds (default: 5000)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.recv_window = recv_window

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        """
        Apply Binance authentication to the request.

        Args:
            headers: Request headers (modified in-place)
            params: Request parameters (modified in-place)
        """
        # Add API key to headers
        headers["X-MBX-APIKEY"] = self.api_key

        # Add timestamp (milliseconds since epoch)
        timestamp = int(time.time() * 1000)
        params["timestamp"] = str(timestamp)

        # Add recvWindow if specified
        if self.recv_window:
            params["recvWindow"] = str(self.recv_window)

        # Generate signature
        # Sort parameters and create query string
        query_string = urlencode(sorted(params.items()))

        # Create HMAC SHA256 signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Add signature to parameters
        params["signature"] = signature

    def get_type(self) -> AuthType:
        """Return the authentication type."""
        return AuthType.API_KEY

    def __repr__(self) -> str:
        return "BinanceAuth(api_key='***', api_secret='***')"
