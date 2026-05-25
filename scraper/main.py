import asyncio
import logging
import sys
from pathlib import Path

from database import DatabaseManager
import scraper


def _configure_logging() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _resolve_db_path() -> str:
    project_root = Path(__file__).resolve().parent.parent
    db_dir = project_root / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    return str(db_dir / "salons.db")


async def main() -> None:
    _configure_logging()
    log = logging.getLogger(__name__)

    db_path = _resolve_db_path()
    log.info("Database path resolved to: %s", db_path)

    db_file = Path(db_path)
    if db_file.exists():
        log.info("Deleting existing database for a clean, duplicate-free scrape run...")
        try:
            db_file.unlink()
            for suffix in ("-wal", "-shm"):
                journal_file = db_file.with_name(db_file.name + suffix)
                if journal_file.exists():
                    journal_file.unlink()
        except Exception as exc:
            log.warning("Could not delete database journals: %s", exc)

    with DatabaseManager(db_path=db_path) as db_manager:
        await scraper.run(db_manager)

    log.info("Scraping complete. Database written to: %s", db_path)


if __name__ == "__main__":
    asyncio.run(main())
