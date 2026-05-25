from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType


@dataclass(slots=True, frozen=True)
class SalonRecord:
    """Represents a single beauty salon's core information."""

    name: str
    address: str
    district: str
    website: str | None
    price_range: str | None
    rating: float | None
    review_count: int | None


@dataclass(slots=True, frozen=True)
class ServiceRecord:
    """Represents a service offered by a salon."""

    name: str
    price: float


@dataclass(slots=True)
class DatabaseManager:
    """Manages SQLite database connections and data insertion for the scraper."""

    db_path: str = field(default="../data/salons.db")
    _connection: sqlite3.Connection = field(init=False, default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Initialize the database connection and schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")
        self._create_tables()

    def _create_tables(self) -> None:
        """Create the Salons and Services tables if they do not exist."""
        self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS Salons (
                Id          INTEGER PRIMARY KEY AUTOINCREMENT,
                Name        TEXT    NOT NULL,
                Address     TEXT    NOT NULL,
                District    TEXT    NOT NULL,
                Website     TEXT,
                PriceRange  TEXT,
                Rating      REAL,
                ReviewCount INTEGER
            );

            CREATE TABLE IF NOT EXISTS Services (
                Id       INTEGER PRIMARY KEY AUTOINCREMENT,
                SalonId  INTEGER NOT NULL REFERENCES Salons(Id) ON DELETE CASCADE,
                Name     TEXT    NOT NULL,
                Price    REAL    NOT NULL DEFAULT 0.0
            );

            CREATE INDEX IF NOT EXISTS idx_salons_district ON Salons(District);
        """)
        self._connection.commit()

    def salon_exists(self, name: str) -> bool:
        """Check if a salon with the given name already exists in the database."""
        row = self._connection.execute(
            "SELECT 1 FROM Salons WHERE Name = ? LIMIT 1", (name,)
        ).fetchone()
        return row is not None

    def count_salons(self) -> int:
        """Return the total number of salons currently in the database."""
        return self._connection.execute("SELECT COUNT(*) FROM Salons").fetchone()[0]

    def insert_salon(self, record: SalonRecord) -> int:
        """Insert a new salon record and return its primary key ID."""
        cursor = self._connection.execute(
            """
            INSERT INTO Salons
                (Name, Address, District, Website, PriceRange, Rating, ReviewCount)
            VALUES
                (:name, :address, :district, :website, :price_range, :rating, :review_count)
            """,
            {
                "name": record.name,
                "address": record.address,
                "district": record.district,
                "website": record.website,
                "price_range": record.price_range,
                "rating": record.rating,
                "review_count": record.review_count,
            },
        )
        self._connection.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def insert_services(self, salon_id: int, services: list[ServiceRecord]) -> None:
        """Insert a list of services associated with a specific salon ID."""
        if not services:
            return
        self._connection.executemany(
            "INSERT INTO Services (SalonId, Name, Price) VALUES (?, ?, ?)",
            [(salon_id, svc.name, svc.price) for svc in services],
        )
        self._connection.commit()

    def __enter__(self) -> DatabaseManager:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._connection.close()
