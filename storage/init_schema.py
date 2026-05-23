# storage/init_schema.py
# One-time schema initializer. Run with: python -m storage.init_schema

import os
import pathlib
import clickhouse_connect
from storage.clickhouse import client


def init():
    # Ensure database exists by connecting to 'default' first
    print("[init_schema] Verifying database existence...")
    default_ch = clickhouse_connect.get_client(
        host=os.environ["CH_HOST"],
        port=int(os.environ.get("CH_PORT", "8443")),
        username=os.environ["CH_USER"],
        password=os.environ["CH_PASSWORD"],
        database="default",
        secure=True,
    )
    default_ch.command("CREATE DATABASE IF NOT EXISTS outbreak")
    print("[init_schema] Database 'outbreak' ready.")

    sql_path = pathlib.Path(__file__).parent / "schema.sql"
    ddl = sql_path.read_text(encoding="utf-8")
    ch = client()
    for statement in ddl.split(";"):
        stmt = statement.strip()
        if stmt:
            ch.command(stmt)
            print(f"[init_schema] executed: {stmt[:60]}...")
    print("[init_schema] schema ready.")


if __name__ == "__main__":
    init()
