"""
HTTP JSON-RPC client for MCP protocol communication.

Includes retry logic with exponential backoff and circuit breaker pattern.
"""

import asyncio
import time
from enum import Enum
from typing import Any, Dict, Optional
import httpx
from pydantic import BaseModel

from .logger import JsonLogger


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_sec: int = 30,
        half_open_max_calls: int = 1
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_sec: Time to wait before attempting recovery
            half_open_max_calls: Max calls to allow in half-open state
        """
        self.failure_threshold = failure_threshold
        self.timeout_sec = timeout_sec
        self.half_open_max_calls = half_open_max_calls

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0

    def call(self, func):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.timeout_sec
            ):
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise Exception(f"Circuit breaker is OPEN")

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise Exception(f"Circuit breaker HALF_OPEN max calls reached")
            self.half_open_calls += 1

        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


class MCPClient:
    """
    HTTP JSON-RPC client for MCP protocol.

    Features:
    - Async HTTP requests
    - Retry logic with exponential backoff
    - Circuit breaker for fault tolerance
    - Comprehensive logging
    """

    def __init__(
        self,
        logger: Optional[JsonLogger] = None,
        max_retries: int = 3,
        backoff_base_sec: int = 1,
        timeout_sec: int = 5,
        circuit_breaker_enabled: bool = True
    ):
        """
        Initialize MCP client.

        Args:
            logger: Optional logger instance
            max_retries: Maximum retry attempts
            backoff_base_sec: Base delay for exponential backoff
            timeout_sec: HTTP request timeout
            circuit_breaker_enabled: Enable circuit breaker
        """
        self.logger = logger
        self.max_retries = max_retries
        self.backoff_base_sec = backoff_base_sec
        self.timeout_sec = timeout_sec
        self.circuit_breaker_enabled = circuit_breaker_enabled

        # Circuit breakers per endpoint
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Async HTTP client
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(timeout=self.timeout_sec)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()

    def _get_circuit_breaker(self, endpoint: str) -> CircuitBreaker:
        """Get or create circuit breaker for endpoint"""
        if endpoint not in self._circuit_breakers:
            self._circuit_breakers[endpoint] = CircuitBreaker()
        return self._circuit_breakers[endpoint]

    async def call_tool(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call MCP tool via JSON-RPC.

        Args:
            endpoint: Target endpoint URL
            method: RPC method name
            params: Method parameters (includes message envelope)
            timeout: Optional custom timeout

        Returns:
            Response result dictionary

        Raises:
            Exception: On failure after all retries
        """
        request_timeout = timeout or self.timeout_sec

        # Build JSON-RPC request
        rpc_request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # Circuit breaker check
                if self.circuit_breaker_enabled:
                    circuit_breaker = self._get_circuit_breaker(endpoint)

                    def _make_request():
                        return self._execute_request(
                            endpoint, rpc_request, request_timeout
                        )

                    # Execute with circuit breaker
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, circuit_breaker.call,
                        lambda: asyncio.run(_make_request())
                    )
                else:
                    result = await self._execute_request(
                        endpoint, rpc_request, request_timeout
                    )

                # Success
                if self.logger:
                    self.logger.debug(
                        "MCP_CALL_SUCCESS",
                        endpoint=endpoint,
                        method=method,
                        attempt=attempt + 1
                    )
                return result

            except Exception as e:
                last_exception = e

                if self.logger:
                    self.logger.warning(
                        "MCP_CALL_RETRY",
                        endpoint=endpoint,
                        method=method,
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        error=str(e)
                    )

                # Last attempt, don't wait
                if attempt == self.max_retries - 1:
                    break

                # Exponential backoff
                delay = self.backoff_base_sec * (2 ** attempt)
                await asyncio.sleep(delay)

        # All retries failed
        if self.logger:
            self.logger.error(
                "MCP_CALL_FAILED",
                endpoint=endpoint,
                method=method,
                error=str(last_exception)
            )

        raise Exception(
            f"MCP call failed after {self.max_retries} retries: {last_exception}"
        )

    async def _execute_request(
        self,
        endpoint: str,
        rpc_request: Dict,
        timeout: int
    ) -> Dict[str, Any]:
        """
        Execute HTTP request.

        Args:
            endpoint: Target URL
            rpc_request: JSON-RPC request
            timeout: Request timeout

        Returns:
            Response result

        Raises:
            Exception: On HTTP error or invalid response
        """
        if not self._client:
            self._client = httpx.AsyncClient(timeout=timeout)

        response = await self._client.post(endpoint, json=rpc_request)

        # Check HTTP status
        response.raise_for_status()

        # Parse JSON-RPC response
        rpc_response = response.json()

        # Check for JSON-RPC error
        if "error" in rpc_response:
            error = rpc_response["error"]
            raise Exception(
                f"JSON-RPC error {error.get('code')}: {error.get('message')}"
            )

        # Return result
        return rpc_response.get("result", {})

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
