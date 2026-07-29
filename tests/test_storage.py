"""
US-8: Position Storage & Indexing (SQLite)
Given/When/Then Gherkin TDD tests + implementation.
"""
import sqlite3
import pytest

DB_PATH = ":memory:"


def setup_storage_db():
    """Given FEN strings and metadata need persistent storage, When the DB is set up, Then a SQLite DB is ready."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fen TEXT UNIQUE NOT NULL,
            label TEXT,
            difficulty TEXT DEFAULT 'medium',
            opening TEXT DEFAULT 'unknown',
            phase TEXT DEFAULT 'unknown',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def insert_positions(conn, positions: list):
    """Given a SQLite connection and list of positions, When insert_positions is called, Then positions are stored."""
    for pos in positions:
        conn.execute(
            "INSERT OR IGNORE INTO positions (fen, label, difficulty, opening, phase) VALUES (?, ?, ?, ?, ?)",
            (
                pos.get("fen"),
                pos.get("label"),
                pos.get("difficulty", "medium"),
                pos.get("opening", "unknown"),
                pos.get("phase", "unknown"),
            ),
        )
    conn.commit()


def query_by_opening(conn, opening: str) -> list:
    """Given a SQLite DB and an opening name, When query_by_opening is called, Then matching positions are returned."""
    cursor = conn.execute(
        "SELECT fen, label, difficulty, phase FROM positions WHERE opening = ?", (opening,)
    )
    return cursor.fetchall()


def query_by_phase(conn, phase: str) -> list:
    """Given a SQLite DB and a phase name, When query_by_phase is called, Then matching positions are returned."""
    cursor = conn.execute(
        "SELECT fen, label, difficulty, opening FROM positions WHERE phase = ?", (phase,)
    )
    return cursor.fetchall()


class TestStorageGivenWhenThen:
    """
    Given FEN strings and metadata need persistent storage,
    When positions are generated or queried,
    Then SQLite FEN index with opening/phase metadata supports fast lookups by position type.
    """

    def test_insert_100_positions_query_by_opening(self):
        """Given 100 positions, When stored in SQLite and queried by opening, Then the correct subset is returned."""
        conn = setup_storage_db()
        positions = [
            {
                "fen": f"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "label": "draw",
                "opening": "opening",
                "phase": "opening",
            }
            for _ in range(100)
        ]
        # Make FENs unique by varying the halfmove clock
        for i, pos in enumerate(positions):
            pos["fen"] = pos["fen"].replace(" - 0 1", f" - {i} 1")
        insert_positions(conn, positions)
        results = query_by_opening(conn, "opening")
        assert len(results) == 100, f"Expected 100 positions for opening, got {len(results)}"

    def test_query_by_opening_returns_correct_subset(self):
        """Given positions with different openings, When queried by opening, Then only matching positions are returned."""
        conn = setup_storage_db()
        positions = [
            {"fen": f"fen_{i}", "label": "win", "opening": "e4", "phase": "opening"}
            for i in range(10)
        ] + [
            {"fen": f"fen_{i+10}", "label": "loss", "opening": "d4", "phase": "opening"}
            for i in range(10)
        ]
        insert_positions(conn, positions)
        e4_results = query_by_opening(conn, "e4")
        d4_results = query_by_opening(conn, "d4")
        assert len(e4_results) == 10, f"Expected 10 e4 positions, got {len(e4_results)}"
        assert len(d4_results) == 10, f"Expected 10 d4 positions, got {len(d4_results)}"

    def test_query_by_phase_returns_correct_positions(self):
        """Given positions with different phases, When queried by phase, Then matching positions are returned."""
        conn = setup_storage_db()
        positions = [
            {"fen": f"fen_{i}", "label": "win", "opening": "e4", "phase": "opening"}
            for i in range(5)
        ] + [
            {"fen": f"fen_{i+5}", "label": "loss", "opening": "e4", "phase": "endgame"}
            for i in range(5)
        ]
        insert_positions(conn, positions)
        opening_results = query_by_phase(conn, "opening")
        endgame_results = query_by_phase(conn, "endgame")
        assert len(opening_results) == 5, f"Expected 5 opening positions, got {len(opening_results)}"
        assert len(endgame_results) == 5, f"Expected 5 endgame positions, got {len(endgame_results)}"

    def test_empty_db_query_returns_empty_list(self):
        """Given an empty DB, When queried by opening, Then an empty list is returned."""
        conn = setup_storage_db()
        results = query_by_opening(conn, "e4")
        assert results == [], f"Empty DB should return empty list, got {results}"

    def test_positions_stored_with_all_metadata(self):
        """Given a position with full metadata, When stored in SQLite, Then all fields are preserved."""
        conn = setup_storage_db()
        positions = [{
            "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            "label": "win",
            "difficulty": "hard",
            "opening": "e4",
            "phase": "opening",
        }]
        insert_positions(conn, positions)
        cursor = conn.execute("SELECT fen, label, difficulty, opening, phase FROM positions WHERE fen = ?", (positions[0]["fen"],))
        row = cursor.fetchone()
        assert row is not None, "Position should be stored"
        assert row[1] == "win", f"Label should be 'win', got {row[1]}"
        assert row[2] == "hard", f"Difficulty should be 'hard', got {row[2]}"
        assert row[3] == "e4", f"Opening should be 'e4', got {row[3]}"
        assert row[4] == "opening", f"Phase should be 'opening', got {row[4]}"

    def test_duplicate_fen_inserted_once(self):
        """Given a position inserted twice, When queried, Then only one copy exists."""
        conn = setup_storage_db()
        positions = [{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "label": "draw", "opening": "e4", "phase": "opening"}]
        insert_positions(conn, positions)
        insert_positions(conn, positions)
        cursor = conn.execute("SELECT COUNT(*) FROM positions")
        count = cursor.fetchone()[0]
        assert count == 1, f"Duplicate FEN should be stored once, got {count}"
