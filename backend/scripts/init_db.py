from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / "backend"))

from app.config import get_settings  # noqa: E402
from app.db import db_cursor, get_server_connection  # noqa: E402


def split_sql(sql: str) -> list[str]:
    statements = []
    current = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip(";"))
            current = []
    if current:
        statements.append("\n".join(current))
    return statements


def main() -> int:
    settings = get_settings()
    with get_server_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()

    sql_path = PROJECT_DIR / "database" / "init.sql"
    sql_text = sql_path.read_text(encoding="utf-8")

    # 初始化脚本一次执行多个 DDL/DML，失败时由 db_cursor 统一回滚并暴露错误。
    with db_cursor() as cursor:
        for statement in split_sql(sql_text):
            cursor.execute(statement)
    print("数据库初始化完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
