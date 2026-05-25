import pytest

from database_builder_libs.models.abstract_relational_store import AbstractRelationalStore
from database_builder_libs.stores.sqlite._relational import SqliteRelationalStore


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
        cur = store.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_schema_version'")
        assert cur.fetchone() is not None

    def test_migration_runs_on_init(self, store):
        cur = store.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_items'")
        assert cur.fetchone() is not None


class TestExecute:
    def test_insert_and_select(self, store):
        store.execute("INSERT INTO test_items(id, label) VALUES (?, ?)", (1, "hello"))
        cur = store.execute("SELECT label FROM test_items WHERE id=?", (1,))
        assert cur.fetchone()[0] == "hello"

    def test_multiple_rows(self, store):
        store.executemany(
            "INSERT INTO test_items(id, label) VALUES (?, ?)",
            [(1, "a"), (2, "b")],
        )
        cur = store.execute("SELECT COUNT(*) FROM test_items")
        assert cur.fetchone()[0] == 2

    def test_commit_persists_changes(self, store):
        store.execute("INSERT INTO test_items(id, label) VALUES (?, ?)", (1, "a"))
        store.commit()
        cur = store.execute("SELECT COUNT(*) FROM test_items")
        assert cur.fetchone()[0] == 1


class TestClose:
    def test_close_is_idempotent(self, store):
        store.close()
        store.close()

    def test_raises_after_close(self, store):
        store.close()
        with pytest.raises(Exception):
            store.execute("SELECT 1")

    def test_cursor_after_close(self, store):
        store.close()
        with pytest.raises(Exception):
            store.cursor()


class TestSchemaMigration:
    def test_migration_only_runs_once(self, store):
        cur = store.execute("SELECT MAX(version) FROM _schema_version")
        assert cur.fetchone()[0] == 1

    def test_subclass_custom_schema(self):
        s = _TestStore(db_path=":memory:")
        try:
            cur = s.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_items'")
            assert cur.fetchone() is not None
        finally:
            s.close()


class TestAbstractInterface:
    def test_sqlite_is_instance(self, store):
        assert isinstance(store, AbstractRelationalStore)
