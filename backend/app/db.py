from contextlib import contextmanager
from typing import Iterator

from app.config import get_settings

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:  # pragma: no cover - 依赖未安装时健康检查会返回不可用
    pymysql = None
    DictCursor = None


def get_connection():
    if pymysql is None:
        raise RuntimeError("PyMySQL is not installed")

    settings = get_settings()
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=2,
        read_timeout=2,
        write_timeout=2,
    )


def get_server_connection():
    if pymysql is None:
        raise RuntimeError("PyMySQL is not installed")

    settings = get_settings()
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=2,
        read_timeout=2,
        write_timeout=2,
    )


@contextmanager
def db_cursor() -> Iterator:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def check_mysql() -> bool:
    try:
        with db_cursor() as cursor:
            cursor.execute("SELECT 1 AS ok")
            row = cursor.fetchone()
            return bool(row and row.get("ok") == 1)
    except Exception:
        return False
