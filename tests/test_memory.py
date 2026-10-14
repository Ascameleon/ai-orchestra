import sqlite3

import pytest

from orchestra.memory import ProviderOutcome, SQLiteProviderMemory


def test_sqlite_provider_memory_persists_aggregate_outcomes_without_task_content(tmp_path):
    database = tmp_path / "provider-memory.sqlite3"
    memory = SQLiteProviderMemory(str(database))
    memory.record(" Gemini ", succeeded=True, duration_ms=12)
    memory.record("gemini", succeeded=False, duration_ms=8)
    memory.record("openai", succeeded=True, duration_ms=-3)

    assert memory.snapshot() == (
        ProviderOutcome("gemini", 1, 1, 20),
        ProviderOutcome("openai", 1, 0, 0),
    )
    memory.close()

    reopened = SQLiteProviderMemory(str(database))
    assert [(item.provider, item.successes, item.failures, item.total_duration_ms) for item in reopened.snapshot()] == [
        ("gemini", 1, 1, 20),
        ("openai", 1, 0, 0),
    ]
    reopened.close()

    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(provider_outcomes)")}
    assert columns == {"provider", "successes", "failures", "total_duration_ms"}
    assert not {"prompt", "completion", "text", "api_key"} & columns


def test_sqlite_provider_memory_rejects_empty_path():
    with pytest.raises(ValueError, match="database_path"):
        SQLiteProviderMemory(" ")
