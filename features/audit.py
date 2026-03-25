import os
import time
import secrets
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Lazy globals
_initialized = False
_engine = None
_Session = None
_AuditEvent = None


def _generate_id() -> str:
    """Timestamp-based UID: {epoch_ms}_{random_hex_8}  e.g. 1742804870123_a1b2c3d4"""
    return f"{int(time.time() * 1000)}_{secrets.token_hex(8)}"


def _init_db() -> bool:
    global _initialized, _engine, _Session, _AuditEvent

    if _initialized:
        return _engine is not None
    _initialized = True

    database_url = os.getenv("DATABASE_URL")
    db_schema = os.getenv("DB_SCHEMA", "securesphere")

    if not database_url:
        logger.warning("AUDIT: DATABASE_URL not set — audit logging disabled.")
        return False

    try:
        from sqlalchemy import create_engine, Column, String, DateTime, text
        from sqlalchemy.orm import DeclarativeBase, sessionmaker

        _engine = create_engine(database_url, pool_pre_ping=True, pool_size=5, max_overflow=10)

        # Auto-create schema if it doesn't exist
        with _engine.connect() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{db_schema}"'))
            conn.commit()

        class Base(DeclarativeBase):
            pass

        class AuditEvent(Base):
            __tablename__ = "audit_events"
            __table_args__ = {"schema": db_schema}

            id          = Column(String(48),  primary_key=True)
            event_type  = Column(String(32),  nullable=False)
            user_sub    = Column(String(255))
            user_email  = Column(String(255))
            first_name  = Column(String(255))
            last_name   = Column(String(255))
            roles       = Column(String(512))
            auth_method = Column(String(255))
            session_id  = Column(String(255))
            org_name    = Column(String(255))
            ip_address  = Column(String(64))
            user_agent  = Column(String(512))
            timestamp   = Column(DateTime(timezone=True),
                                 default=lambda: datetime.now(timezone.utc))

        # Creates table only if it doesn't exist — never drops existing data
        Base.metadata.create_all(_engine, checkfirst=True)
        
        # Simple auto-migration for newly added columns
        with _engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            for col in ['first_name', 'last_name', 'roles', 'auth_method', 'session_id', 'org_name']:
                try:
                    conn.execute(text(f'ALTER TABLE "{db_schema}"."audit_events" ADD COLUMN "{col}" VARCHAR(512)'))
                except Exception:
                    pass

        _Session = sessionmaker(bind=_engine)
        _AuditEvent = AuditEvent

        logger.info(f"AUDIT: Ready — schema='{db_schema}', table='audit_events'")
        return True

    except Exception as exc:
        logger.error(f"AUDIT: DB init failed — {exc}")
        _engine = None
        _initialized = False   # allow retry on next request
        return False


def log_event(event_type: str, user_info: dict):
    """Log a login/logout event. Silently skips if DB is unavailable."""
    if not _init_db():
        return

    try:
        from flask import request
        ip = request.remote_addr or "unknown"
        ua = request.headers.get("User-Agent", "unknown")
    except Exception:
        ip = ua = "unknown"

    try:
        session = _Session()
        amr_raw = user_info.get("amr", [])
        amr_val = amr_raw[0] if isinstance(amr_raw, list) and amr_raw else str(amr_raw)
        
        event = _AuditEvent(
            id=_generate_id(),
            event_type=event_type,
            user_sub=str(user_info.get("sub", "")),
            user_email=str(user_info.get("email", "")),
            first_name=str(user_info.get("given_name", "")),
            last_name=str(user_info.get("family_name", "")),
            roles=str(user_info.get("roles", "")),
            auth_method=amr_val,
            session_id=str(user_info.get("sid", "")),
            org_name=str(user_info.get("org_name", "")),
            ip_address=ip,
            user_agent=ua[:512],
            timestamp=datetime.now(timezone.utc),
        )
        session.add(event)
        session.commit()
        session.close()
        logger.info(f"AUDIT: {event_type} logged for {user_info.get('email', 'unknown')}")
    except Exception as exc:
        logger.error(f"AUDIT: Failed to write event — {exc}")


def get_events(limit: int = 100) -> list:
    """Return recent audit events as list of dicts."""
    if not _init_db():
        return []

    try:
        session = _Session()
        rows = (
            session.query(_AuditEvent)
            .order_by(_AuditEvent.timestamp.desc())
            .limit(limit)
            .all()
        )
        result = [
            {
                "id":         r.id,
                "event_type": r.event_type,
                "user_email": r.user_email or "",
                "user_sub":   r.user_sub or "",
                "first_name": r.first_name or "",
                "last_name":  r.last_name or "",
                "roles":      r.roles or "",
                "auth_method":r.auth_method or "",
                "session_id": r.session_id or "",
                "org_name":   r.org_name or "",
                "ip_address": r.ip_address or "",
                "user_agent": r.user_agent or "",
                "timestamp":  (
                    r.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
                    if r.timestamp else ""
                ),
            }
            for r in rows
        ]
        session.close()
        return result
    except Exception as exc:
        logger.error(f"AUDIT: Failed to read events — {exc}")
        return []
