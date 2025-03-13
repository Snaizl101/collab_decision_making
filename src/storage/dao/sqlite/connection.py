import sqlite3
from pathlib import Path
import threading
from contextlib import contextmanager
from typing import Optional
import logging

from src.storage.dao.exceptions import ConnectionError, QueryError, DAOError


class SQLiteConnection:
    """
    Handles SQLite database connections with thread-safe connection management.
    Provides initialization and transaction handling.
    """

    def __init__(self, db_path: Path, schema_path: Optional[Path] = None):
        """
        Initialize connection manager.

        Args:
            db_path: Path to SQLite database file
            schema_path: Optional custom schema file path

        Raises:
            ConnectionError: If database initialization fails
        """
        self.db_path = db_path
        self.schema_path = schema_path or Path(__file__).parent / 'schema.sql'
        self._local = threading.local()
        self.logger = logging.getLogger(__name__)
        self._initialize_db()

    def _initialize_db(self) -> None:
        """
        Initialize database with schema if needed

        Raises:
            ConnectionError: If database or schema initialization fails
        """
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            with self.get_connection() as conn:
                try:
                    with open(self.schema_path) as f:
                        conn.executescript(f.read())
                    self.logger.info("Database initialized successfully")
                except (IOError, sqlite3.Error) as e:
                    self.logger.error(f"Failed to read or execute schema: {e}")
                    raise ConnectionError(f"Schema initialization failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise ConnectionError(f"Database initialization failed: {str(e)}")

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Get or create thread-local database connection.

        Returns:
            sqlite3.Connection: Database connection for current thread

        Raises:
            ConnectionError: If connection creation fails
        """
        if not hasattr(self._local, 'connection'):
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                self._local.connection = conn
            except sqlite3.Error as e:
                raise ConnectionError(f"Failed to create database connection: {str(e)}")
        return self._local.connection

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        try:
            yield self.connection
        except sqlite3.Error as e:
            self.logger.error(f"Database operation failed: {e}")
            self.connection.rollback()
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during database operation: {e}")
            self.connection.rollback()
            raise DAOError(f"Unexpected database error: {str(e)}")

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        Automatically commits on success or rolls back on error.
        """
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except sqlite3.IntegrityError as e:
                self.logger.error(f"Integrity error in transaction: {e}")
                conn.rollback()
                # Re-raise the original SQLite integrity error
                raise
            except sqlite3.Error as e:
                self.logger.error(f"Transaction failed: {e}")
                conn.rollback()
                raise QueryError(f"Transaction failed: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error during transaction: {e}")
                conn.rollback()
                raise DAOError(f"Unexpected transaction error: {str(e)}")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a single SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            sqlite3.Cursor: Query cursor

        Raises:
            QueryError: On query execution error
        """
        try:
            with self.get_connection() as conn:
                return conn.execute(query, params)
        except sqlite3.Error as e:
            raise QueryError(f"Query execution failed: {str(e)}")

    def execute_many(self, query: str, params_list: list) -> sqlite3.Cursor:
        """
        Execute multiple SQL queries in a single transaction.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            sqlite3.Cursor: Query cursor

        Raises:
            QueryError: On query execution error
        """
        try:
            with self.transaction() as conn:
                return conn.executemany(query, params_list)
        except sqlite3.Error as e:
            raise QueryError(f"Batch query execution failed: {str(e)}")

    def query_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        """
        Execute a query and return one result row.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Optional[dict]: Result row as dictionary or None if no results

        Raises:
            QueryError: On query execution error
        """
        try:
            cursor = self.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            raise QueryError(f"Query execution failed: {str(e)}")

    def query_all(self, query: str, params: tuple = ()) -> list[dict]:
        """
        Execute a query and return all result rows.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            list[dict]: List of result rows as dictionaries

        Raises:
            QueryError: On query execution error
        """
        try:
            cursor = self.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise QueryError(f"Query execution failed: {str(e)}")

    def close(self) -> None:
        """
        Close the current thread's database connection if it exists

        Raises:
            ConnectionError: If connection closure fails
        """
        if hasattr(self._local, 'connection'):
            try:
                self._local.connection.close()
                delattr(self._local, 'connection')
            except sqlite3.Error as e:
                self.logger.error(f"Error closing connection: {e}")
                raise ConnectionError(f"Failed to close database connection: {str(e)}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed"""
        self.close()