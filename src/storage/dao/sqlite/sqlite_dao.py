from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import sqlite3

from storage.dao.base import DataAccessInterface
from storage.dao.sqlite.connection import SQLiteConnection
from storage.dao.exceptions import DAOError, DataIntegrityError, RecordNotFoundError, QueryError


class SQLiteDAO(DataAccessInterface):
    """SQLite implementation of the data access interface"""

    def __init__(self, db_path: Path):
        """Initialize SQLite DAO with database path"""
        try:
            self.conn = SQLiteConnection(db_path)
        except Exception as e:
            raise DAOError(f"Failed to initialize DAO: {str(e)}")

    def store_recording(self, recording_id: str, file_path: Path,
                       duration: int, recording_date: datetime,
                       format: str) -> None:
        """Store metadata for a new recording"""
        try:
            with self.conn.transaction() as conn:
                conn.execute("""
                    INSERT INTO recordings 
                    (recording_id, file_path, duration, recording_date, format)
                    VALUES (?, ?, ?, ?, ?)
                """, (recording_id, str(file_path), duration,
                     recording_date.isoformat(), format))
        except sqlite3.IntegrityError as e:
            # Handle integrity violations
            if "UNIQUE constraint failed" in str(e):
                raise DataIntegrityError(
                    f"Recording {recording_id} already exists: {str(e)}"
                )
            raise DataIntegrityError(f"Data integrity error: {str(e)}")
        except QueryError as e:
            # Handle query-related errors
            raise DAOError(f"Query error while storing recording: {str(e)}")
        except Exception as e:
            # Handle any other errors
            raise DAOError(f"Failed to store recording: {str(e)}")

    def store_transcription(self, recording_id: str,
                            segments: List[Dict[str, Any]]) -> None:
        """Store transcription segments for a recording"""
        try:
            with self.conn.transaction() as conn:
                conn.executemany("""
                    INSERT INTO transcriptions 
                    (recording_id, speaker_id, start_time, end_time, text, confidence)
                    VALUES (:recording_id, :speaker_id, :start_time, :end_time, 
                           :text, :confidence)
                """, [{**segment, 'recording_id': recording_id} for segment in segments])
        except sqlite3.IntegrityError as e:
            raise DataIntegrityError(f"Invalid transcription data: {str(e)}")
        except Exception as e:
            raise DAOError(f"Failed to store transcription: {str(e)}")

    def store_topic(self, recording_id: str, topic_data: Dict[str, Any]) -> int:
        """Store an identified topic"""
        try:
            cursor = self.conn.execute("""
                INSERT INTO topics 
                (recording_id, topic_name, start_time, end_time, importance_score)
                VALUES (:recording_id, :topic_name, :start_time, :end_time, 
                       :importance_score)
            """, {**topic_data, 'recording_id': recording_id})
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise DataIntegrityError(f"Invalid topic data: {str(e)}")
        except Exception as e:
            raise DAOError(f"Failed to store topic: {str(e)}")

    def store_argument(self, recording_id: str, topic_id: int,
                       argument_data: Dict[str, Any]) -> int:
        """Store an analyzed argument"""
        try:
            cursor = self.conn.execute("""
                INSERT INTO arguments 
                (recording_id, topic_id, speaker_id, start_time, end_time,
                 argument_text, argument_type, conclusion)
                VALUES (:recording_id, :topic_id, :speaker_id, :start_time, :end_time,
                       :argument_text, :argument_type, :conclusion)
            """, {**argument_data, 'recording_id': recording_id, 'topic_id': topic_id})
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise DataIntegrityError(f"Invalid argument data: {str(e)}")
        except Exception as e:
            raise DAOError(f"Failed to store argument: {str(e)}")

    def store_agreement(self, recording_id: str, argument_id: int,
                        agreement_data: Dict[str, Any]) -> int:
        """Store agreement/disagreement information"""
        try:
            cursor = self.conn.execute("""
                INSERT INTO agreements 
                (recording_id, argument_id, speaker_id, agreement_type,
                 confidence_score, timestamp)
                VALUES (:recording_id, :argument_id, :speaker_id, :agreement_type,
                       :confidence_score, :timestamp)
            """, {**agreement_data, 'recording_id': recording_id,
                  'argument_id': argument_id})
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise DataIntegrityError(f"Invalid agreement data: {str(e)}")
        except Exception as e:
            raise DAOError(f"Failed to store agreement: {str(e)}")

    def store_gap(self, recording_id: str, topic_id: Optional[int],
                  gap_data: Dict[str, Any]) -> int:
        """Store identified discussion gaps or suggestions"""
        try:
            cursor = self.conn.execute("""
                INSERT INTO gaps 
                (recording_id, topic_id, gap_type, description, importance_score)
                VALUES (:recording_id, :topic_id, :gap_type, :description,
                       :importance_score)
            """, {**gap_data, 'recording_id': recording_id, 'topic_id': topic_id})
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise DataIntegrityError(f"Invalid gap data: {str(e)}")
        except Exception as e:
            raise DAOError(f"Failed to store gap: {str(e)}")

    def get_recording_metadata(self, recording_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve recording metadata"""
        try:
            result = self.conn.query_one("""
                SELECT * FROM recordings WHERE recording_id = ?
            """, (recording_id,))
            if result is None:
                raise RecordNotFoundError(f"Recording {recording_id} not found")
            return result
        except RecordNotFoundError:
            raise
        except Exception as e:
            raise DAOError(f"Failed to get recording metadata: {str(e)}")

    def get_transcription(self, recording_id: str,
                          start_time: Optional[float] = None,
                          end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """Retrieve transcription segments"""
        try:
            query = """
                SELECT * FROM transcriptions 
                WHERE recording_id = ?
            """
            params = [recording_id]

            if start_time is not None:
                query += " AND end_time >= ?"
                params.append(start_time)
            if end_time is not None:
                query += " AND start_time <= ?"
                params.append(end_time)

            query += " ORDER BY start_time"
            return self.conn.query_all(query, tuple(params))
        except Exception as e:
            raise DAOError(f"Failed to get transcription: {str(e)}")

    def get_topics(self, recording_id: str) -> List[Dict[str, Any]]:
        """Retrieve all topics for a recording"""
        try:
            return self.conn.query_all("""
                SELECT * FROM topics 
                WHERE recording_id = ?
                ORDER BY start_time
            """, (recording_id,))
        except Exception as e:
            raise DAOError(f"Failed to get topics: {str(e)}")

    def get_arguments(self, recording_id: str,
                      topic_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve arguments for a recording"""
        try:
            query = """
                SELECT * FROM arguments 
                WHERE recording_id = ?
            """
            params = [recording_id]

            if topic_id is not None:
                query += " AND topic_id = ?"
                params.append(topic_id)

            query += " ORDER BY start_time"
            return self.conn.query_all(query, tuple(params))
        except Exception as e:
            raise DAOError(f"Failed to get arguments: {str(e)}")

    def get_agreements(self, recording_id: str,
                       argument_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve agreements for a recording"""
        try:
            query = """
                SELECT * FROM agreements 
                WHERE recording_id = ?
            """
            params = [recording_id]

            if argument_id is not None:
                query += " AND argument_id = ?"
                params.append(argument_id)

            query += " ORDER BY timestamp"
            return self.conn.query_all(query, tuple(params))
        except Exception as e:
            raise DAOError(f"Failed to get agreements: {str(e)}")

    def get_gaps(self, recording_id: str,
                 topic_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve identified gaps for a recording"""
        try:
            query = """
                SELECT * FROM gaps 
                WHERE recording_id = ?
            """
            params = [recording_id]

            if topic_id is not None:
                query += " AND topic_id = ?"
                params.append(topic_id)

            return self.conn.query_all(query, tuple(params))
        except Exception as e:
            raise DAOError(f"Failed to get gaps: {str(e)}")

    def get_discussion_summary(self, recording_id: str) -> Dict[str, Any]:
        """Retrieve a complete summary of the discussion"""
        try:
            return {
                'metadata': self.get_recording_metadata(recording_id),
                'topics': self.get_topics(recording_id),
                'arguments': self.get_arguments(recording_id),
                'agreements': self.get_agreements(recording_id),
                'gaps': self.get_gaps(recording_id)
            }
        except RecordNotFoundError:
            raise
        except Exception as e:
            raise DAOError(f"Failed to get discussion summary: {str(e)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()