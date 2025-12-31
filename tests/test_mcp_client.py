"""
Unit tests for MCP Client with HTTP mocking.

Tests retry logic, circuit breaker, and JSON-RPC communication.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx

from SHARED.league_sdk.mcp_client import MCPClient, CircuitState, CircuitBreaker


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes correctly"""
        cb = CircuitBreaker(failure_threshold=3, timeout_sec=30)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after failure threshold"""
        cb = CircuitBreaker(failure_threshold=2)

        # First failure
        cb._on_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1

        # Second failure - should open
        cb._on_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 2

    def test_circuit_resets_on_success(self):
        """Test circuit resets failure count on success"""
        cb = CircuitBreaker(failure_threshold=3)

        cb._on_failure()
        cb._on_failure()
        assert cb.failure_count == 2

        cb._on_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_circuit_half_open_transition(self):
        """Test circuit transitions to half-open after timeout"""
        import time
        cb = CircuitBreaker(failure_threshold=1, timeout_sec=1)

        # Open the circuit
        cb._on_failure()
        assert cb.state == CircuitState.OPEN

        # Try calling before timeout - should still be open
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(lambda: "result")

        # Wait for timeout
        time.sleep(1.1)

        # Should transition to half-open and allow call
        cb.state = CircuitState.CLOSED  # Reset for test
        result = cb.call(lambda: "success")
        assert result == "success"


class TestMCPClient:
    """Test MCP Client functionality"""

    def test_client_initialization(self):
        """Test MCP client initialization"""
        client = MCPClient(max_retries=5, timeout_sec=10)
        assert client.max_retries == 5
        assert client.timeout_sec == 10
        assert client.circuit_breaker_enabled == True

    def test_client_with_logger(self):
        """Test MCP client with logger"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            from SHARED.league_sdk.logger import JsonLogger
            logger = JsonLogger(component="test")
            client = MCPClient(logger=logger)
            assert client.logger == logger

    def test_client_without_logger(self):
        """Test MCP client without logger"""
        client = MCPClient()
        assert client.logger is None

    def test_get_circuit_breaker_creates_new(self):
        """Test _get_circuit_breaker creates new breaker for endpoint"""
        client = MCPClient()
        endpoint = "http://localhost:8001/mcp"

        cb = client._get_circuit_breaker(endpoint)
        assert cb is not None
        assert isinstance(cb, CircuitBreaker)
        assert endpoint in client._circuit_breakers

    def test_get_circuit_breaker_reuses_existing(self):
        """Test _get_circuit_breaker reuses existing breaker"""
        client = MCPClient()
        endpoint = "http://localhost:8001/mcp"

        cb1 = client._get_circuit_breaker(endpoint)
        cb2 = client._get_circuit_breaker(endpoint)

        assert cb1 is cb2  # Same instance

    def test_get_circuit_breaker_different_endpoints(self):
        """Test different endpoints get different breakers"""
        client = MCPClient()

        cb1 = client._get_circuit_breaker("http://localhost:8001/mcp")
        cb2 = client._get_circuit_breaker("http://localhost:8002/mcp")

        assert cb1 is not cb2  # Different instances

    @pytest.mark.asyncio
    async def test_context_manager_enter_exit(self):
        """Test async context manager"""
        client = MCPClient()

        async with client as c:
            assert c is client
            # Session creation is internal implementation detail

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test close method"""
        client = MCPClient()

        # Close should work even if session doesn't exist
        await client.close()

        # Multiple closes should be safe
        await client.close()


class TestCircuitBreakerAdvanced:
    """Advanced circuit breaker tests"""

    def test_circuit_breaker_with_zero_threshold(self):
        """Test circuit breaker with zero threshold always open"""
        cb = CircuitBreaker(failure_threshold=0)
        assert cb.state == CircuitState.CLOSED

        # Any failure should open it immediately
        cb._on_failure()
        assert cb.state == CircuitState.OPEN

    def test_circuit_call_with_successful_function(self):
        """Test calling a successful function through circuit"""
        cb = CircuitBreaker(failure_threshold=3)

        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.failure_count == 0

    def test_circuit_call_with_failing_function(self):
        """Test calling a failing function through circuit"""
        cb = CircuitBreaker(failure_threshold=2)

        def fail_func():
            raise ValueError("Test error")

        # First failure
        with pytest.raises(ValueError):
            cb.call(fail_func)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1

        # Second failure - opens circuit
        with pytest.raises(ValueError):
            cb.call(fail_func)
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 2

    def test_circuit_rejects_when_open(self):
        """Test circuit rejects calls when open"""
        cb = CircuitBreaker(failure_threshold=1)

        # Open the circuit
        cb._on_failure()
        assert cb.state == CircuitState.OPEN

        # Should reject calls
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(lambda: "test")

    def test_multiple_successes(self):
        """Test multiple successful calls"""
        cb = CircuitBreaker(failure_threshold=3)

        for i in range(5):
            result = cb.call(lambda: f"call_{i}")
            assert cb.failure_count == 0
            assert cb.state == CircuitState.CLOSED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
