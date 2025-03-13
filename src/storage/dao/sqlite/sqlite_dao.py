"""
SQLite DAO module.
Provides data access operations for the SQLite database.
Manages all database interactions for storing and retrieving analysis results.
"""
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import sqlite3

from src.storage.dao.base import DataAccessInterface
from src.storage.dao.sqlite.connection import SQLiteConnection
from src.storage.dao.exceptions import DAOError, DataIntegrityError, RecordNotFoundError, QueryError


class SQLiteDAO(DataAccessInterface):
    """SQLite DAO implementation

    Responsibilities:
    - Store and retrieve:
        - audio metadata
        - transcribe data
        - topic analysis data
        - sentiment analysis data

    Key Tables:
    - recordings: Audio file metadata
    - transcriptions: Transcribed segments
    - topics: Identified discussion topics
    - sentiment_analysis: Sentiment scores and data
    """

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
                    (recording_id, speaker_id, start_time, end_time, text)
                    VALUES (:recording_id, :speaker_id, :start_time, :end_time, 
                           :text)
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
                (recording_id, topic_name, start_time, end_time)
                VALUES (:recording_id, :topic_name, :start_time, :end_time)
            """, {**topic_data, 'recording_id': recording_id})
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise DataIntegrityError(f"Invalid topic data: {str(e)}")
        except Exception as e:
            raise DAOError(f"Failed to store topic: {str(e)}")

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

    # Add to src/storage/dao/sqlite/sqlite_dao.py

    def store_sentiment(self, recording_id: str, sentiment_data: Dict[str, Any]) -> int:
        """Store sentiment analysis result"""
        try:
            cursor = self.conn.execute("""
                INSERT INTO sentiment_analysis 
                (recording_id, speaker_id, timestamp, sentiment_score, text)
                VALUES (:recording_id, :speaker_id, :timestamp, :sentiment_score, 
                        :text)
            """, {**sentiment_data, 'recording_id': recording_id})
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise DataIntegrityError(f"Invalid sentiment data: {str(e)}")
        except Exception as e:
            raise DAOError(f"Failed to store sentiment: {str(e)}")

    def get_sentiment_analysis(self, recording_id: str) -> Dict[str, Any]:
        """Get complete sentiment analysis for a recording"""
        try:
            # Get all sentiment entries
            sentiment_entries = self.conn.query_all("""
                SELECT * FROM sentiment_analysis 
                WHERE recording_id = ?
                ORDER BY timestamp
            """, (recording_id,))

            # Calculate overall sentiment
            if not sentiment_entries:
                return {
                    'overall_sentiment': 0,
                    'sentiment_timeline': [],
                    'speaker_sentiments': {}
                }

            # Calculate per-speaker averages
            speaker_totals = {}
            speaker_counts = {}
            for entry in sentiment_entries:
                speaker = entry['speaker_id']
                if speaker not in speaker_totals:
                    speaker_totals[speaker] = 0
                    speaker_counts[speaker] = 0
                speaker_totals[speaker] += entry['sentiment_score']
                speaker_counts[speaker] += 1

            speaker_sentiments = {
                speaker: speaker_totals[speaker] / speaker_counts[speaker]
                for speaker in speaker_totals
            }

            # Calculate overall sentiment
            overall_sentiment = sum(entry['sentiment_score'] for entry in sentiment_entries) / len(sentiment_entries)

            return {
                'overall_sentiment': overall_sentiment,
                'sentiment_timeline': [
                    {
                        'timestamp': entry['timestamp'],
                        'sentiment_score': entry['sentiment_score'],
                        'speaker_id': entry['speaker_id'],
                        'text': entry['text']
                    }
                    for entry in sentiment_entries
                ],
                'speaker_sentiments': speaker_sentiments
            }
        except Exception as e:
            raise DAOError(f"Failed to get sentiment analysis: {str(e)}")

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
