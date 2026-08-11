from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def build_engine(
    database_url: str,
    *,
    busy_timeout_ms: int | None = None,
    enable_wal: bool | None = None,
) -> Engine:
    url = make_url(database_url)
    is_sqlite = url.get_backend_name() == "sqlite"
    timeout_ms = busy_timeout_ms or settings.sqlite_busy_timeout_ms
    wal_enabled = settings.sqlite_wal_enabled if enable_wal is None else enable_wal
    connect_args = (
        {"check_same_thread": False, "timeout": timeout_ms / 1000}
        if is_sqlite
        else {}
    )
    database_engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    if is_sqlite:
        is_file_database = bool(url.database and url.database != ":memory:")

        @event.listens_for(database_engine, "connect")
        def configure_sqlite_connection(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute(f"PRAGMA busy_timeout={timeout_ms}")
            if wal_enabled and is_file_database:
                # WAL allows readers to continue while the single production
                # worker writes. SQLite still serializes writes; busy_timeout
                # handles short contention without adding more workers.
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    return database_engine


engine = build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
