"""
Database Migration Scripts

Handles schema updates for existing Transmission databases.
"""

import sqlite3
from pathlib import Path
from loguru import logger
from typing import Optional


class DatabaseMigrations:
    """
    Handle database schema migrations.

    Adds missing columns to existing databases without losing data.
    """

    def __init__(self, db_path: str):
        """
        Initialize migration manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()

    def check_column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table"""
        self.cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in self.cursor.fetchall()]
        return column in columns

    def migrate_gear_columns(self) -> None:
        """
        Add gear-related columns to trades table if they don't exist.

        Adds:
        - gear_at_entry: TEXT (P/R/N/D/L)
        - gear_at_exit: TEXT (P/R/N/D/L)
        - gear_shift_reason_entry: TEXT
        """
        logger.info("Checking for gear column migrations...")

        columns_to_add = [
            ("gear_at_entry", "TEXT"),
            ("gear_at_exit", "TEXT"),
            ("gear_shift_reason_entry", "TEXT")
        ]

        for column_name, column_type in columns_to_add:
            if not self.check_column_exists("trades", column_name):
                logger.info(f"Adding column {column_name} to trades table...")
                try:
                    self.cursor.execute(f"""
                        ALTER TABLE trades
                        ADD COLUMN {column_name} {column_type}
                    """)
                    self.conn.commit()
                    logger.success(f"Added {column_name} column")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
                    logger.info(f"Column {column_name} already exists")
            else:
                logger.info(f"Column {column_name} already exists")

    def migrate_gear_shifts_table(self) -> None:
        """Create gear_shifts table if it doesn't exist"""
        logger.info("Checking for gear_shifts table...")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS gear_shifts (
                shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                from_gear TEXT NOT NULL,
                to_gear TEXT NOT NULL,
                reason TEXT NOT NULL,

                -- Context at time of shift
                daily_r REAL NOT NULL,
                weekly_r REAL NOT NULL,
                consecutive_losses INTEGER NOT NULL,
                current_drawdown REAL,
                regime TEXT,
                volatility_percentile REAL,
                mental_state INTEGER,
                dll_remaining REAL,
                tripwire_active BOOLEAN,
                in_trading_session BOOLEAN,
                news_blackout_active BOOLEAN,
                kill_switch_active BOOLEAN,
                positions_open INTEGER
            )
        """)
        self.conn.commit()
        logger.success("gear_shifts table verified")

    def run_all_migrations(self) -> None:
        """Run all pending migrations"""
        logger.info("Running database migrations...")

        try:
            self.migrate_gear_columns()
            self.migrate_gear_shifts_table()
            logger.success("All migrations completed successfully")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.conn.rollback()
            raise
        finally:
            self.conn.close()


def migrate_database(db_path: Optional[str] = None) -> None:
    """
    Run migrations on a database.

    Args:
        db_path: Path to database file (uses default if None)
    """
    if db_path is None:
        db_path = Path(__file__).parent.parent / "data" / "transmission.db"

    if not Path(db_path).exists():
        logger.info(f"Database {db_path} does not exist yet, skipping migrations")
        return

    logger.info(f"Migrating database: {db_path}")
    migrations = DatabaseMigrations(str(db_path))
    migrations.run_all_migrations()


if __name__ == "__main__":
    # Run migrations on default database
    migrate_database()

    # Also migrate user-specific databases
    user_data_dir = Path(__file__).parent.parent.parent / "data"
    if user_data_dir.exists():
        for user_db in user_data_dir.glob("user_*/transmission.db"):
            migrate_database(str(user_db))
