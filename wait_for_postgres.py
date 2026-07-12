import os
import time

import psycopg2
from psycopg2 import OperationalError


def wait_for_postgres(dsn: str, retries: int = 20, delay: int = 2) -> None:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(dsn, connect_timeout=3)
            conn.close()
            print("Postgres is available.")
            return
        except OperationalError as exc:
            last_error = exc
            print(f"Postgres not ready yet (attempt {attempt}/{retries}): {exc}")
            time.sleep(delay)

    raise RuntimeError(f"Could not connect to Postgres after {retries} attempts: {last_error}")


if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")

    wait_for_postgres(database_url)
