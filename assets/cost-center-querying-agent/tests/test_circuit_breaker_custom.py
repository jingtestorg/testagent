"""Tests for circuit breaker module."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_circuit_breaker_allows_when_no_failures(add_agent_to_path):
    """Test circuit breaker allows requests with no failures."""
    from circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
    result = await breaker.allows("test-model")
    assert result is True


@pytest.mark.asyncio
async def test_circuit_breaker_record_failure(add_agent_to_path):
    """Test recording a failure increments the counter."""
    from circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
    await breaker.record_failure("test-model")
    # Still allows since threshold not hit
    result = await breaker.allows("test-model")
    assert result is True


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold(add_agent_to_path):
    """Test circuit breaker opens after threshold failures."""
    from circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=100)
    await breaker.record_failure("test-model")
    await breaker.record_failure("test-model")
    result = await breaker.allows("test-model")
    assert result is False


@pytest.mark.asyncio
async def test_circuit_breaker_record_success_resets(add_agent_to_path):
    """Test recording success resets failure count."""
    from circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=100)
    await breaker.record_failure("test-model")
    await breaker.record_success("test-model")
    # After success, failures reset
    result = await breaker.allows("test-model")
    assert result is True


@pytest.mark.asyncio
async def test_circuit_breaker_multiple_models_independent(add_agent_to_path):
    """Test that circuit breaker tracks models independently."""
    from circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=100)
    await breaker.record_failure("model-a")
    await breaker.record_failure("model-a")
    # model-a should be open
    assert await breaker.allows("model-a") is False
    # model-b should still be allowed
    assert await breaker.allows("model-b") is True
