from __future__ import annotations

import datetime
import os
import shutil
from pathlib import Path


APP_NAME = "MiniERP"


def resolve_base_dir() -> Path:
    if getattr(os, "frozen", False):
        return Path(os.path.dirname(os.path.abspath(os.path.realpath(os.sys.executable))))
    return Path(__file__).resolve().parent


def ensure_directories(base_dir: Path) -> dict[str, Path]:
    directories = {
        "db": base_dir / "database.db",
        "backups": base_dir / "backups",
        "invoices": base_dir / "invoices",
        "reports": base_dir / "reports",
    }
    for key, path in directories.items():
        if key == "db":
            continue
        path.mkdir(parents=True, exist_ok=True)
    return directories


def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_database(db_path: Path, backups_dir: Path) -> Path | None:
    if not db_path.exists():
        return None
    backup_path = backups_dir / f"database_backup_{timestamp()}.db"
    try:
        shutil.copy2(db_path, backup_path)
    except (OSError, shutil.Error):
        return None
    return backup_path


def safe_write_text(path: Path, content: str) -> bool:
    try:
        path.write_text(content, encoding="utf-8")
    except OSError:
        return False
    return True


def pendrive_available(base_dir: Path) -> bool:
    try:
        return base_dir.exists() and base_dir.is_dir()
    except OSError:
        return False
