from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType


@dataclass(slots=True, frozen=True)
class SalonRecord:
    name: str
    address: str
    district: str
    phone: str | None
    website: str | None
    price_range: str | None
    rating: float | None
    review_count: int | None


@dataclass(slots=True, frozen=True)
class ServiceRecord:
    name: str
    price: float


@dataclass(slots=True)
class DatabaseManager:
    db_path: str = field(default="../data/salons.db")
    _connection: sqlite3.Connection = field(init=False)

    def __post_init__(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")
        self.setup_tables()

    def setup_tables(self) -> None:
        self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS Salons (
                Id          INTEGER PRIMARY KEY AUTOINCREMENT,
                Name        TEXT    NOT NULL,
                Address     TEXT    NOT NULL,
                District    TEXT    NOT NULL,
                PhoneNumber TEXT,
                Website     TEXT,
                PriceRange  TEXT,
                Rating      REAL,
                ReviewCount INTEGER,
                ScrapedAt   DATETIME DEFAULT CURRENT_TIMESTAMP
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

    def insert_salon(self, record: SalonRecord) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO Salons (Name, Address, District, PhoneNumber, Website, PriceRange, Rating, ReviewCount)
            VALUES (:name, :address, :district, :phone, :website, :price_range, :rating, :review_count)
            """,
            {
                "name": record.name,
                "address": record.address,
                "district": record.district,
                "phone": record.phone,
                "website": record.website,
                "price_range": record.price_range,
                "rating": record.rating,
                "review_count": record.review_count,
            },
        )
        self._connection.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def insert_services(self, salon_id: int, services: list[ServiceRecord]) -> None:
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
