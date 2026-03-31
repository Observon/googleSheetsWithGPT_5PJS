"""Tests for cache adapter."""

import tempfile

import pytest

from src.adapters.cache import CacheAdapter


@pytest.fixture
def cache_adapter():
    """Create a cache adapter with temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield CacheAdapter(cache_dir=tmpdir)


def test_cache_set_and_get(cache_adapter):
    """Test setting and getting cache."""
    spreadsheet_id = "sheet-123"
    prompt = "What is the average?"
    result = "The average is 42."

    # Set cache
    success = cache_adapter.set(spreadsheet_id, prompt, result)
    assert success

    # Get cache
    cached_result = cache_adapter.get(spreadsheet_id, prompt)
    assert cached_result == result


def test_cache_exists(cache_adapter):
    """Test checking if cache entry exists."""
    spreadsheet_id = "sheet-123"
    prompt = "What is the average?"

    # Should not exist
    assert not cache_adapter.exists(spreadsheet_id, prompt)

    # After setting
    cache_adapter.set(spreadsheet_id, prompt, "Result")
    assert cache_adapter.exists(spreadsheet_id, prompt)


def test_cache_miss(cache_adapter):
    """Test cache miss returns None."""
    result = cache_adapter.get("nonexistent", "nonexistent")
    assert result is None


def test_cache_clear(cache_adapter):
    """Test clearing all cache."""
    # Add multiple entries
    for i in range(3):
        cache_adapter.set(f"sheet-{i}", "prompt", f"result-{i}")

    # Clear
    count = cache_adapter.clear()
    assert count == 3

    # Verify cleared
    for i in range(3):
        assert not cache_adapter.exists(f"sheet-{i}", "prompt")


def test_cache_delete_key(cache_adapter):
    """Test deleting a specific cache key."""
    spreadsheet_id = "sheet-123"
    prompt = "What is the average?"

    # Set cache
    cache_adapter.set(spreadsheet_id, prompt, "Result")
    assert cache_adapter.exists(spreadsheet_id, prompt)

    # Delete
    success = cache_adapter.delete_key(spreadsheet_id, prompt)
    assert success
    assert not cache_adapter.exists(spreadsheet_id, prompt)


def test_cache_delete_nonexistent(cache_adapter):
    """Test deleting non-existent entry."""
    success = cache_adapter.delete_key("nonexistent", "nonexistent")
    assert not success


def test_cache_different_prompts(cache_adapter):
    """Test that different prompts have different cache entries."""
    spreadsheet_id = "sheet-123"

    cache_adapter.set(spreadsheet_id, "prompt-a", "result-a")
    cache_adapter.set(spreadsheet_id, "prompt-b", "result-b")

    assert cache_adapter.get(spreadsheet_id, "prompt-a") == "result-a"
    assert cache_adapter.get(spreadsheet_id, "prompt-b") == "result-b"
