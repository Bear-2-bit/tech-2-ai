import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings


def now() -> str:
    return datetime.now(UTC).isoformat()


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, parent_id TEXT, module TEXT NOT NULL, name TEXT NOT NULL,
                    status TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, latency_ms REAL,
                    input_tokens INTEGER, output_tokens INTEGER, error TEXT, result TEXT, metadata TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS run_parent ON runs(parent_id);
                CREATE INDEX IF NOT EXISTS run_started ON runs(started_at);
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY, run_id TEXT, level TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, document_id TEXT NOT NULL, filename TEXT NOT NULL, content_hash TEXT NOT NULL,
                    version INTEGER NOT NULL, status TEXT NOT NULL, chunk_count INTEGER NOT NULL DEFAULT 0,
                    metadata TEXT NOT NULL, created_at TEXT NOT NULL, error TEXT,
                    UNIQUE(document_id, version)
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, messages TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS eval_results (
                    run_id TEXT NOT NULL, case_id TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(run_id, case_id)
                );
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def execute(self, sql: str, parameters=()) -> None:
        with self.connection() as db:
            db.execute(sql, parameters)

    def rows(self, sql: str, parameters=()) -> list[dict]:
        with self.connection() as db:
            return [dict(row) for row in db.execute(sql, parameters).fetchall()]

    def run(self, run_id: str) -> dict | None:
        rows = self.rows("SELECT * FROM runs WHERE id=?", (run_id,))
        if not rows:
            return None
        row = rows[0]
        for field in ("result", "metadata"):
            row[field] = json.loads(row[field]) if row[field] else None
        return row

    def event(self, run_id: str | None, message: str, level: str = "INFO") -> None:
        self.execute(
            "INSERT INTO events(run_id,level,message,created_at) VALUES(?,?,?,?)", (run_id, level, message, now())
        )

    def usage(self, run_id: str, input_tokens: int, output_tokens: int) -> None:
        with self.connection() as db:
            current = run_id
            while current:
                db.execute(
                    "UPDATE runs SET input_tokens=COALESCE(input_tokens,0)+?, "
                    "output_tokens=COALESCE(output_tokens,0)+? WHERE id=?",
                    (input_tokens, output_tokens, current),
                )
                row = db.execute("SELECT parent_id FROM runs WHERE id=?", (current,)).fetchone()
                current = row[0] if row else None


@lru_cache
def get_store() -> Store:
    return Store(get_settings().app_database_path)
