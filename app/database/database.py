"""Database Connection & Session Management."""

from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings
from app.database.models import Base
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.database")

_engine = None
_session_factory = None


def get_db_path() -> Path:
    settings = get_settings()
    return settings.DATA_DIR / "autoweb.db"


def init_db(db_path: Optional[Path] = None) -> sessionmaker[Session]:
    """Khởi tạo SQLite database và tạo các bảng nếu chưa có."""
    global _engine, _session_factory
    target_path = db_path or get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite:///{target_path}"
    logger.info(f"Khởi tạo SQLite database tại: {db_url}")

    _engine = create_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False},  # Cho phép SQLite chạy đa luồng an toàn
    )
    
    # Tạo schema tables
    Base.metadata.create_all(bind=_engine)

    _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _session_factory


def get_db_session() -> Session:
    """Cung cấp một database session độc lập."""
    global _session_factory
    if _session_factory is None:
        init_db()
    return _session_factory()

