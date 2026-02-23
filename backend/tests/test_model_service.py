"""
Unit tests for RFC §1.5 — Model Service Optimization Beyond Instance Caching

Covers:
- Canonical cache key normalizations (max_tokens, temperature)
- API-key fingerprint inclusion and invalidation behaviour
- Separate streaming / non-streaming semaphores
- invalidate_cache() method
"""
import asyncio
import hashlib
import os
import pytest

# ---------------------------------------------------------------------------
# Environment bootstrap — must happen before any app import
# ---------------------------------------------------------------------------
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key-for-fingerprint")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("LOG_ENABLED", "false")

from app.services.model_service import ModelService, _MODEL_DEFAULTS, _DEFAULT_MAX_TOKENS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fingerprint(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Test §1: max_tokens=None and max_tokens=<model default> map to the same key
# ---------------------------------------------------------------------------

class TestCanonicalKeyMaxTokens:
    """max_tokens normalisation: None and model-default both collapse to None."""

    def test_none_and_model_default_produce_same_key_gpt4o(self):
        fp = _fingerprint("key")
        key_none = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        key_default = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=128000,  # gpt-4o model default
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        assert key_none == key_default, (
            "max_tokens=None and max_tokens=128000 (model default) must map to the same cache entry"
        )

    def test_none_and_model_default_produce_same_key_gpt4o_mini(self):
        fp = _fingerprint("key")
        key_none = ModelService._canonical_key(
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        key_default = ModelService._canonical_key(
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=128000,  # gpt-4o-mini model default
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        assert key_none == key_default

    def test_below_default_max_tokens_is_preserved(self):
        """max_tokens=512 (well below model default) must NOT be collapsed."""
        fp = _fingerprint("key")
        key_none = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        key_512 = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=512,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        assert key_none != key_512, (
            "max_tokens=512 must produce a different cache key than max_tokens=None"
        )

    def test_max_tokens_preserved_in_key_for_small_value(self):
        """Verify the effective_max component is 512, not None."""
        fp = _fingerprint("key")
        key = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=512,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        # key[2] is the effective_max slot
        assert key[2] == 512

    def test_max_tokens_zero_collapses_to_none(self):
        """max_tokens=0 is not a valid positive limit and must collapse to None (not pass the > 0 guard)."""
        fp = _fingerprint("key")
        key_zero = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=0,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        key_none = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        # key[2] is the effective_max slot — both must be None
        assert key_zero[2] is None
        assert key_zero == key_none, (
            "max_tokens=0 must produce the same cache key as max_tokens=None"
        )


# ---------------------------------------------------------------------------
# Test §2: temperature=0.70 and temperature=0.7 resolve to the same key
# ---------------------------------------------------------------------------

class TestCanonicalKeyTemperature:
    """temperature normalisation: rounded to 1 decimal place."""

    def test_0_70_and_0_7_same_key(self):
        fp = _fingerprint("key")
        key_70 = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.70,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        key_7 = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        assert key_70 == key_7

    def test_0_75_and_0_7_different_keys(self):
        fp = _fingerprint("key")
        key_75 = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.75,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        key_7 = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        # 0.75 rounds to 0.8, which differs from 0.7
        assert key_75 != key_7

    def test_temperature_stored_rounded(self):
        fp = _fingerprint("key")
        key = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.70000001,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp,
        )
        # key[1] is the effective_temp slot
        assert key[1] == 0.7


# ---------------------------------------------------------------------------
# Test §3: Different api_key_fingerprint values produce different keys
# ---------------------------------------------------------------------------

class TestCanonicalKeyFingerprint:
    """API-key fingerprint differentiation."""

    def test_different_fingerprints_produce_different_keys(self):
        fp1 = _fingerprint("api-key-one")
        fp2 = _fingerprint("api-key-two")
        assert fp1 != fp2, "Test pre-condition: fingerprints must differ"

        key1 = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp1,
        )
        key2 = ModelService._canonical_key(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=None,
            json_mode=False,
            stream=False,
            api_key_fingerprint=fp2,
        )
        assert key1 != key2

    def test_same_fingerprint_same_key(self):
        fp = _fingerprint("same-api-key")
        key1 = ModelService._canonical_key("gpt-4o", 0.7, None, False, False, fp)
        key2 = ModelService._canonical_key("gpt-4o", 0.7, None, False, False, fp)
        assert key1 == key2

    def test_fingerprint_is_8_hex_chars(self):
        fp = _fingerprint("any-key")
        assert len(fp) == 8
        assert all(c in "0123456789abcdef" for c in fp)

    def test_api_key_rotation_invalidates_cache(self):
        """Rotating the API key causes _get_llm() to build a new cache entry."""
        svc = ModelService()

        # Patch settings to return a predictable key then swap it
        import app.services.model_service as ms_module
        from unittest.mock import patch, MagicMock

        fake_llm = MagicMock()

        with patch("app.services.model_service.ChatOpenAI", return_value=fake_llm):
            with patch.object(type(svc), "_api_key_fingerprint",
                              new_callable=lambda: property(lambda self: "aaaaaaaa")):
                svc._get_llm("gpt-4o", 0.7, None, False, False)
                size_before = len(svc._llm_cache)

            with patch.object(type(svc), "_api_key_fingerprint",
                              new_callable=lambda: property(lambda self: "bbbbbbbb")):
                svc._get_llm("gpt-4o", 0.7, None, False, False)
                size_after = len(svc._llm_cache)

        # Two distinct fingerprints → two distinct cache entries
        assert size_after == size_before + 1


# ---------------------------------------------------------------------------
# Test §4: invalidate_cache() clears the cache and returns count
# ---------------------------------------------------------------------------

class TestInvalidateCache:
    """invalidate_cache() contract."""

    def test_returns_count_of_cleared_entries(self):
        svc = ModelService()
        # Directly seed the cache to avoid real API calls
        svc._llm_cache[("gpt-4o", 0.7, None, False, False, "aa")] = object()
        svc._llm_cache[("gpt-4o-mini", 0.5, None, False, False, "bb")] = object()
        assert len(svc._llm_cache) == 2

        cleared = svc.invalidate_cache(reason="test")
        assert cleared == 2

    def test_cache_is_empty_after_invalidation(self):
        svc = ModelService()
        svc._llm_cache[("gpt-4o", 0.7, None, False, False, "cc")] = object()
        svc.invalidate_cache()
        assert len(svc._llm_cache) == 0

    def test_invalidate_empty_cache_returns_zero(self):
        svc = ModelService()
        assert len(svc._llm_cache) == 0
        result = svc.invalidate_cache(reason="no-op")
        assert result == 0

    def test_cache_repopulates_after_invalidation(self):
        """After clearing, _get_llm() creates a fresh entry."""
        svc = ModelService()
        from unittest.mock import patch, MagicMock

        fake_llm = MagicMock()
        with patch("app.services.model_service.ChatOpenAI", return_value=fake_llm):
            with patch.object(type(svc), "_api_key_fingerprint",
                              new_callable=lambda: property(lambda self: "deadbeef")):
                svc._get_llm("gpt-4o", 0.7, None, False, False)
                assert len(svc._llm_cache) == 1

                svc.invalidate_cache()
                assert len(svc._llm_cache) == 0

                svc._get_llm("gpt-4o", 0.7, None, False, False)
                assert len(svc._llm_cache) == 1


# ---------------------------------------------------------------------------
# Test §5: Semaphore configuration
# ---------------------------------------------------------------------------

class TestSemaphores:
    """Verify the semaphore capacity limits are correct."""

    def test_streaming_semaphore_limit_is_10(self):
        svc = ModelService()
        # asyncio.Semaphore exposes _value for introspection
        assert svc._streaming_semaphore._value == 10

    def test_sync_semaphore_limit_is_25(self):
        svc = ModelService()
        assert svc._sync_semaphore._value == 25

    def test_semaphores_have_correct_limits(self):
        """Each ModelService instance has semaphores with the correct capacity."""
        svc = ModelService()
        assert svc._streaming_semaphore._value == 10
        assert svc._sync_semaphore._value == 25
