import pytest

from database_builder_libs.models.abstract_relational_store import AbstractRelationalStore
from database_builder_libs.stores.sqlite.relational import SqliteRelationalStore


class _TestStore(SqliteRelationalStore):
    SCHEMA_VERSION = 1

    def _run_migrations(self, from_version: int) -> None:
        if from_version < 1:
            self.execute("CREATE TABLE IF NOT EXISTS test_items(id INTEGER PRIMARY KEY, label TEXT)")


@pytest.fixture
def store():
    s = _TestStore(db_path=":memory:")
    yield s
    s.close()


class TestConnection:
    def test_in_memory(self):
        s = SqliteRelationalStore(db_path=":memory:")
        s.close()

    def test_schema_version_table_created(self, store):
        rows = store.query_raw("SELECT name FROM sqlite_master WHERE type='table' AND name='_schema_version'")
        assert len(rows) == 1

    def test_migration_runs_on_init(self, store):
        rows = store.query_raw("SELECT name FROM sqlite_master WHERE type='table' AND name='test_items'")
        assert len(rows) == 1


class TestExecute:
    def test_insert_and_select(self, store):
        store.execute("INSERT INTO test_items(id, label) VALUES (?, ?)", (1, "hello"))
        rows = store.query("test_items", {"id": 1})
        assert rows[0]["label"] == "hello"

    def test_multiple_queries(self, store):
        store.execute("INSERT INTO test_items(id, label) VALUES (?, ?)", (1, "a"))
        store.execute("INSERT INTO test_items(id, label) VALUES (?, ?)", (2, "b"))
        rows = store.query_raw("SELECT COUNT(*) AS cnt FROM test_items")
        assert rows[0]["cnt"] == 2

    def test_commit_persists_changes(self, store):
        store.execute("INSERT INTO test_items(id, label) VALUES (?, ?)", (1, "a"))
        store.commit()
        rows = store.query_raw("SELECT COUNT(*) AS cnt FROM test_items")
        assert rows[0]["cnt"] == 1


class TestClose:
    def test_close_is_idempotent(self, store):
        store.close()
        store.close()

    def test_raises_after_close(self, store):
        store.close()
        with pytest.raises(Exception):
            store.execute("SELECT 1")


class TestSchemaMigration:
    def test_migration_only_runs_once(self, store):
        rows = store.query_raw("SELECT MAX(version) AS v FROM _schema_version")
        assert rows[0]["v"] == 1

    def test_subclass_custom_schema(self):
        s = _TestStore(db_path=":memory:")
        try:
            rows = s.query_raw("SELECT name FROM sqlite_master WHERE type='table' AND name='test_items'")
            assert len(rows) == 1
        finally:
            s.close()


class TestAbstractInterface:
    def test_sqlite_is_instance(self, store):
        assert isinstance(store, AbstractRelationalStore)


class TestInsert:
    def test_insert_single_row(self, store):
        store.insert("test_items", {"id": 1, "label": "hello"})
        rows = store.query("test_items", {"id": 1})
        assert len(rows) == 1
        assert rows[0]["label"] == "hello"

    def test_insert_commits_implicitly(self, store):
        store.insert("test_items", {"id": 1, "label": "hello"})
        rows = store.query("test_items", None)
        assert len(rows) == 1


class TestQuery:
    def test_query_with_filter(self, store):
        store.insert("test_items", {"id": 1, "label": "a"})
        store.insert("test_items", {"id": 2, "label": "b"})
        rows = store.query("test_items", {"label": "a"})
        assert len(rows) == 1
        assert rows[0]["id"] == 1

    def test_query_no_filter(self, store):
        store.insert("test_items", {"id": 1, "label": "a"})
        store.insert("test_items", {"id": 2, "label": "b"})
        rows = store.query("test_items")
        assert len(rows) == 2

    def test_query_none_filter(self, store):
        store.insert("test_items", {"id": 1, "label": "a"})
        rows = store.query("test_items", None)
        assert len(rows) == 1

    def test_query_empty_result(self, store):
        rows = store.query("test_items", {"id": 999})
        assert rows == []


class TestUpdate:
    def test_update_existing_row(self, store):
        store.insert("test_items", {"id": 1, "label": "old"})
        count = store.update("test_items", {"id": 1}, {"label": "new"})
        assert count == 1
        rows = store.query("test_items", {"id": 1})
        assert rows[0]["label"] == "new"

    def test_update_no_match(self, store):
        count = store.update("test_items", {"id": 999}, {"label": "nope"})
        assert count == 0


class TestDelete:
    def test_delete_existing_row(self, store):
        store.insert("test_items", {"id": 1, "label": "a"})
        count = store.delete("test_items", {"id": 1})
        assert count == 1
        rows = store.query("test_items", {"id": 1})
        assert rows == []

    def test_delete_no_match(self, store):
        count = store.delete("test_items", {"id": 999})
        assert count == 0


class TestQueryRaw:
    def test_query_raw_simple(self, store):
        store.insert("test_items", {"id": 1, "label": "hello"})
        rows = store.query_raw("SELECT label FROM test_items WHERE id=?", (1,))
        assert rows[0]["label"] == "hello"

    def test_query_raw_no_params(self, store):
        store.insert("test_items", {"id": 1, "label": "a"})
        rows = store.query_raw("SELECT COUNT(*) AS cnt FROM test_items")
        assert rows[0]["cnt"] == 1
