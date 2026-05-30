import time
from datetime import datetime

import pytest

from database_builder_libs.utility.sync._sqlite import SqliteSyncTracker


@pytest.fixture
def tracker():
    tracker = SqliteSyncTracker(db_path=":memory:")
    tracker.connect()
    yield tracker
    tracker.close()


@pytest.fixture
def fresh_tracker():
    """Return a tracker factory that creates a fresh in-memory tracker."""
    instances = []

    def _make(**kwargs):
        tracker = SqliteSyncTracker(db_path=":memory:", **kwargs)
        tracker.connect()
        instances.append(tracker)
        return tracker

    yield _make
    for instance in instances:
        instance.close()


class TestStartSync:
    def test_new_source_returns_none(self, tracker):
        last_sync = tracker.start_sync("Zotero")
        assert last_sync is None

    def test_existing_source_returns_timestamp(self, tracker):
        tracker.start_sync("Zotero")
        artifacts = [("item-1", datetime.fromtimestamp(100))]
        tracker.finish_sync("Zotero", artifacts)
        last_sync = tracker.start_sync("Zotero")
        assert isinstance(last_sync, float)
        assert last_sync > 0

    def test_unknown_source_does_not_affect_others(self, tracker):
        tracker.start_sync("SourceA")
        artifacts = [("item-1", datetime.fromtimestamp(100))]
        tracker.finish_sync("SourceA", artifacts)
        last_sync_b = tracker.start_sync("SourceB")
        assert last_sync_b is None


class TestFinishSync:
    def test_empty_artifacts_returns_no_conflicts(self, tracker):
        tracker.start_sync("Zotero")
        conflicts = tracker.finish_sync("Zotero", [])
        assert conflicts == []

    def test_new_artifacts_are_stored(self, tracker):
        tracker.start_sync("Zotero")
        conflicts = tracker.finish_sync(
            "Zotero",
            [("item-1", datetime.fromtimestamp(100))],
        )
        assert conflicts == []

    def test_artifacts_are_upserted(self, tracker):
        tracker.start_sync("Zotero")
        tracker.finish_sync("Zotero", [("item-1", datetime.fromtimestamp(100))])
        history = tracker.sync_history("Zotero")
        assert len(history) == 1
        assert history[0]["item_key"] == "item-1"
        assert history[0]["modified_time"] == 100

    def test_artifacts_update_on_resync(self, tracker):
        tracker.start_sync("Zotero")
        tracker.finish_sync("Zotero", [("item-1", datetime.fromtimestamp(100))])
        tracker.finish_sync("Zotero", [("item-1", datetime.fromtimestamp(200))])
        history = tracker.sync_history("Zotero")
        assert history[0]["modified_time"] == 200

    def test_updates_source_timestamp(self, tracker):
        tracker.start_sync("Zotero")
        tracker.finish_sync("Zotero", [("item-1", datetime.fromtimestamp(100))])
        ts1 = tracker.start_sync("Zotero")
        assert isinstance(ts1, float)
        time.sleep(0.01)
        tracker.finish_sync("Zotero", [("item-1", datetime.fromtimestamp(100))])
        ts2 = tracker.start_sync("Zotero")
        assert ts2 > ts1


class TestConflictDetection:
    def test_same_mod_time_no_conflict(self, tracker):
        tracker.start_sync("SourceA")
        tracker.start_sync("SourceB")
        tracker.finish_sync("SourceA", [("item-1", datetime.fromtimestamp(100))])
        conflicts = tracker.finish_sync(
            "SourceB", [("item-1", datetime.fromtimestamp(100))]
        )
        assert conflicts == []

    def test_different_mod_time_detects_conflict(self, tracker):
        tracker.start_sync("SourceA")
        tracker.start_sync("SourceB")
        tracker.finish_sync("SourceA", [("item-1", datetime.fromtimestamp(100))])
        conflicts = tracker.finish_sync(
            "SourceB", [("item-1", datetime.fromtimestamp(200))]
        )
        assert conflicts == ["item-1"]

    def test_conflict_only_reported_for_current_source(self, tracker):
        tracker.start_sync("SourceA")
        tracker.start_sync("SourceB")
        tracker.start_sync("SourceC")
        tracker.finish_sync("SourceA", [("item-1", datetime.fromtimestamp(100))])
        tracker.finish_sync("SourceB", [("item-1", datetime.fromtimestamp(200))])
        conflicts_c = tracker.finish_sync(
            "SourceC", [("item-1", datetime.fromtimestamp(100))]
        )
        assert "item-1" in conflicts_c

    def test_no_conflict_for_unique_items(self, tracker):
        tracker.start_sync("SourceA")
        tracker.start_sync("SourceB")
        tracker.finish_sync("SourceA", [("item-a", datetime.fromtimestamp(100))])
        conflicts = tracker.finish_sync(
            "SourceB", [("item-b", datetime.fromtimestamp(200))]
        )
        assert conflicts == []

    def test_conflict_clears_after_reconciliation(self, tracker):
        tracker.start_sync("SourceA")
        tracker.start_sync("SourceB")
        tracker.finish_sync("SourceA", [("item-1", datetime.fromtimestamp(100))])
        conflicts = tracker.finish_sync(
            "SourceB", [("item-1", datetime.fromtimestamp(200))]
        )
        assert conflicts == ["item-1"]
        tracker.finish_sync("SourceA", [("item-1", datetime.fromtimestamp(200))])
        tracker.finish_sync("SourceB", [("item-1", datetime.fromtimestamp(200))])
        history = tracker.sync_history("SourceA")
        assert history[0]["modified_time"] == 200


class TestInMemoryDatabase:
    def test_in_memory_works(self):
        tracker = SqliteSyncTracker(db_path=":memory:")
        tracker.connect()
        try:
            last_sync = tracker.start_sync("Zotero")
            assert last_sync is None
        finally:
            tracker.close()


class TestCustomTableNames:
    def test_custom_table_names(self, fresh_tracker):
        tracker = fresh_tracker(table_sources="src", table_artifacts="artf")
        tracker.start_sync("Zotero")
        conflicts = tracker.finish_sync("Zotero", [("item-1", datetime.fromtimestamp(100))])
        assert conflicts == []


class TestInjectionSafety:
    def test_table_sources_injection_raises(self):
        with pytest.raises(ValueError):
            SqliteSyncTracker(db_path=":memory:", table_sources="sources; DROP TABLE")

    def test_table_artifacts_injection_raises(self):
        with pytest.raises(ValueError):
            SqliteSyncTracker(db_path=":memory:", table_artifacts="artifacts; DROP TABLE")

    def test_injection_with_spaces_raises(self):
        with pytest.raises(ValueError):
            SqliteSyncTracker(db_path=":memory:", table_sources="my sources")

    def test_injection_with_digits_start_raises(self):
        with pytest.raises(ValueError):
            SqliteSyncTracker(db_path=":memory:", table_sources="1table")

    def test_legitimate_table_names_pass(self, fresh_tracker):
        t = fresh_tracker(table_sources="custom_src", table_artifacts="custom_artf")
        t.start_sync("Zotero")
        conflicts = t.finish_sync("Zotero", [("item-1", datetime.fromtimestamp(100))])
        assert conflicts == []


class TestCleanupOldRecords:
    def test_removes_old_artifacts(self, tracker):
        tracker.start_sync("Zotero")
        tracker.finish_sync("Zotero", [("item-1", datetime.fromtimestamp(100))])
        now = time.time()
        deleted = tracker.cleanup_old_records(before=now + 1)
        assert deleted == 1
        history = tracker.sync_history("Zotero")
        assert len(history) == 0

    def test_preserves_recent_artifacts(self, tracker):
        tracker.start_sync("Zotero")
        tracker.finish_sync("Zotero", [("item-1", datetime.fromtimestamp(100))])
        before = time.time() - 1
        deleted = tracker.cleanup_old_records(before=before)
        assert deleted == 0


class TestSyncHistory:
    def test_returns_all_artifacts_for_source(self, tracker):
        tracker.start_sync("Zotero")
        tracker.finish_sync(
            "Zotero",
            [
                ("item-1", datetime.fromtimestamp(100)),
                ("item-2", datetime.fromtimestamp(200)),
            ],
        )
        history = tracker.sync_history("Zotero")
        assert len(history) == 2
        keys = {entry["item_key"] for entry in history}
        assert keys == {"item-1", "item-2"}

    def test_empty_history_for_unknown_source(self, tracker):
        history = tracker.sync_history("Unknown")
        assert history == []


class TestSyncStats:
    def test_initial_stats(self, tracker):
        stats = tracker.sync_stats()
        assert stats["total_sources"] == 0
        assert stats["total_artifacts"] == 0
        assert stats["sources_with_conflicts"] == 0

    def test_stats_after_sync(self, tracker):
        tracker.start_sync("SourceA")
        tracker.finish_sync("SourceA", [("item-1", datetime.fromtimestamp(100))])
        stats = tracker.sync_stats()
        assert stats["total_sources"] == 1
        assert stats["total_artifacts"] == 1
        assert stats["sources_with_conflicts"] == 0

    def test_stats_with_conflicts(self, tracker):
        tracker.start_sync("SourceA")
        tracker.start_sync("SourceB")
        tracker.finish_sync("SourceA", [("item-1", datetime.fromtimestamp(100))])
        tracker.finish_sync("SourceB", [("item-1", datetime.fromtimestamp(200))])
        stats = tracker.sync_stats()
        assert stats["sources_with_conflicts"] == 2


class TestClose:
    def test_close_is_idempotent(self, tracker):
        tracker.close()
        tracker.close()

    def test_closed_tracker_raises(self, tracker):
        tracker.close()
        with pytest.raises(RuntimeError, match="before connect"):
            tracker.start_sync("Zotero")

    def test_multiple_trackers_same_file(self, tmp_path):
        db_path = tmp_path / "shared.db"
        tracker_1 = SqliteSyncTracker(db_path=db_path)
        tracker_2 = SqliteSyncTracker(db_path=db_path)
        tracker_1.connect()
        tracker_2.connect()
        try:
            tracker_1.start_sync("SourceA")
            tracker_2.start_sync("SourceB")
            tracker_1.finish_sync("SourceA", [("item-1", datetime.fromtimestamp(100))])
            tracker_2.finish_sync("SourceB", [("item-1", datetime.fromtimestamp(200))])
            assert tracker_1.start_sync("SourceA") is not None
        finally:
            tracker_1.close()
            tracker_2.close()
