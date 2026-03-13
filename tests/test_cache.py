"""Tests for SkillCache."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from cmdop_skill._cache import CacheEntry, SkillCache


@pytest.fixture
def cache(tmp_path: Path) -> SkillCache:
    return SkillCache("test-skill", cache_root=tmp_path)


class TestSkillCache:
    def test_set_and_get(self, cache: SkillCache) -> None:
        cache.set("key1", {"foo": "bar"})
        result = cache.get("key1")
        assert result == {"foo": "bar"}

    def test_get_missing_returns_none(self, cache: SkillCache) -> None:
        assert cache.get("nonexistent") is None

    def test_set_string_value(self, cache: SkillCache) -> None:
        cache.set("mystr", "hello world")
        assert cache.get("mystr") == "hello world"

    def test_set_list_value(self, cache: SkillCache) -> None:
        cache.set("mylist", [1, 2, 3])
        assert cache.get("mylist") == [1, 2, 3]

    def test_set_none_value(self, cache: SkillCache) -> None:
        cache.set("nullval", None)
        assert cache.get("nullval") is None

    def test_ttl_not_expired(self, cache: SkillCache) -> None:
        cache.set("fresh", "data", ttl=3600)
        assert cache.get("fresh") == "data"

    def test_ttl_expired(self, cache: SkillCache) -> None:
        cache.set("stale", "old", ttl=0.01)
        time.sleep(0.05)
        assert cache.get("stale") is None

    def test_ttl_none_never_expires(self, cache: SkillCache) -> None:
        cache.set("permanent", "value", ttl=None)
        assert cache.get("permanent") == "value"

    def test_expired_file_deleted_on_read(self, cache: SkillCache) -> None:
        cache.set("gone", "x", ttl=0.01)
        path = cache._path("gone")
        assert path.exists()
        time.sleep(0.05)
        cache.get("gone")
        assert not path.exists()

    def test_delete_existing(self, cache: SkillCache) -> None:
        cache.set("todel", "v")
        assert cache.delete("todel") is True
        assert cache.get("todel") is None

    def test_delete_missing(self, cache: SkillCache) -> None:
        assert cache.delete("nope") is False

    def test_clear(self, cache: SkillCache) -> None:
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        count = cache.clear()
        assert count == 3
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_clear_empty(self, cache: SkillCache) -> None:
        assert cache.clear() == 0

    def test_is_fresh_true(self, cache: SkillCache) -> None:
        cache.set("fresh", "v")
        assert cache.is_fresh("fresh", ttl=3600) is True

    def test_is_fresh_false_missing(self, cache: SkillCache) -> None:
        assert cache.is_fresh("missing", ttl=3600) is False

    def test_is_fresh_false_old(self, cache: SkillCache) -> None:
        cache.set("old", "v")
        time.sleep(0.05)
        assert cache.is_fresh("old", ttl=0.01) is False

    def test_info_returns_entry(self, cache: SkillCache) -> None:
        cache.set("meta", 42, ttl=3600)
        entry = cache.info("meta")
        assert entry is not None
        assert isinstance(entry, CacheEntry)
        assert entry.value == 42
        assert entry.ttl == 3600
        assert entry.key == "meta"

    def test_info_missing_returns_none(self, cache: SkillCache) -> None:
        assert cache.info("nothing") is None

    def test_info_expired_returns_none(self, cache: SkillCache) -> None:
        cache.set("exp", "v", ttl=0.01)
        time.sleep(0.05)
        assert cache.info("exp") is None

    def test_cache_dir_exists(self, cache: SkillCache) -> None:
        assert cache.cache_dir.is_dir()

    def test_cache_dir_scoped_to_skill(self, tmp_path: Path) -> None:
        c1 = SkillCache("skill-a", cache_root=tmp_path)
        c2 = SkillCache("skill-b", cache_root=tmp_path)
        c1.set("k", "v1")
        c2.set("k", "v2")
        assert c1.get("k") == "v1"
        assert c2.get("k") == "v2"

    def test_key_with_slash_sanitized(self, cache: SkillCache) -> None:
        cache.set("path/to/key", "safe")
        assert cache.get("path/to/key") == "safe"
        # file should exist with sanitized name
        assert (cache.cache_dir / "path_to_key.json").exists()

    def test_overwrite_existing_key(self, cache: SkillCache) -> None:
        cache.set("k", "first")
        cache.set("k", "second")
        assert cache.get("k") == "second"


class TestCacheEntry:
    def test_not_expired_with_no_ttl(self) -> None:
        entry = CacheEntry.create(key="k", value="v", ttl=None)
        assert entry.is_expired is False

    def test_not_expired_fresh(self) -> None:
        entry = CacheEntry.create(key="k", value="v", ttl=3600)
        assert entry.is_expired is False

    def test_expired(self) -> None:
        entry = CacheEntry.create(key="k", value="v", ttl=0.01)
        time.sleep(0.05)
        assert entry.is_expired is True

    def test_serialization_roundtrip(self) -> None:
        entry = CacheEntry.create(key="x", value={"nested": [1, 2]}, ttl=60.0)
        json_str = entry.model_dump_json()
        restored = CacheEntry.model_validate_json(json_str)
        assert restored.key == "x"
        assert restored.value == {"nested": [1, 2]}
        assert restored.ttl == 60.0
