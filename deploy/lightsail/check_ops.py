import os
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"].replace("+asyncpg", "")
engine = create_engine(url)
with engine.connect() as conn:
    rows = conn.execute(
        text(
            "SELECT email, is_platform_operator, first_name, last_name "
            "FROM users ORDER BY created_at"
        )
    ).fetchall()
    for row in rows:
        print(row)
