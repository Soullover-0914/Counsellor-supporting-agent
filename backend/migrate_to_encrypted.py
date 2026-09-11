import sqlite3
from pathlib import Path

from sqlcipher3 import dbapi2 as sqlcipher


BASE_DIR = Path(__file__).resolve().parent

PLAIN_DATABASE = BASE_DIR / "counselling_agent.db"
ENCRYPTED_DATABASE = BASE_DIR / "counselling_agent_encrypted.db"

ENCRYPTION_KEY = "agent66-development-encryption-key-change-before-production"


def get_plain_connection():
    connection = sqlite3.connect(PLAIN_DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def get_encrypted_connection():
    connection = sqlcipher.connect(ENCRYPTED_DATABASE)

    connection.execute(
        f"PRAGMA key = '{ENCRYPTION_KEY}'"
    )

    connection.execute("PRAGMA cipher_compatibility = 4")

    return connection


def migrate_database():
    if not PLAIN_DATABASE.exists():
        raise FileNotFoundError(
            f"Plain database not found: {PLAIN_DATABASE}"
        )

    if ENCRYPTED_DATABASE.exists():
        raise FileExistsError(
            f"Encrypted database already exists: {ENCRYPTED_DATABASE}"
        )

    plain = get_plain_connection()
    encrypted = get_encrypted_connection()

    try:
        plain_tables = plain.execute(
            """
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        if not plain_tables:
            raise RuntimeError(
                "No application tables were found in the plain database."
            )

        print("Tables found in plain database:")

        for table in plain_tables:
            print(f"  - {table['name']}")

        for table in plain_tables:
            table_name = table["name"]
            create_sql = table["sql"]

            print(f"\nCreating table: {table_name}")

            encrypted.execute(create_sql)

            columns = plain.execute(
                f"PRAGMA table_info('{table_name}')"
            ).fetchall()

            column_names = [
                column["name"]
                for column in columns
            ]

            quoted_columns = ", ".join(
                f'"{column}"'
                for column in column_names
            )

            placeholders = ", ".join(
                "?"
                for _ in column_names
            )

            rows = plain.execute(
                f'SELECT {quoted_columns} FROM "{table_name}"'
            ).fetchall()

            print(
                f"Copying {len(rows)} row(s) into {table_name}"
            )

            if rows:
                encrypted.executemany(
                    f"""
                    INSERT INTO "{table_name}"
                    ({quoted_columns})
                    VALUES ({placeholders})
                    """,
                    [
                        tuple(row[column] for column in column_names)
                        for row in rows
                    ],
                )

        encrypted.commit()

        print("\nMigration completed successfully.")

    except Exception:
        encrypted.rollback()
        encrypted.close()

        if ENCRYPTED_DATABASE.exists():
            ENCRYPTED_DATABASE.unlink()

        raise

    finally:
        plain.close()

        try:
            encrypted.close()
        except Exception:
            pass


if __name__ == "__main__":
    migrate_database()

    print(
        f"\nEncrypted database created at:\n"
        f"{ENCRYPTED_DATABASE}"
    )