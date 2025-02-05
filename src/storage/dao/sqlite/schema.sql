-- Initial schema for Discussion Analysis System


-- Store recording metadata
CREATE TABLE IF NOT EXISTS recordings
(
    recording_id   TEXT PRIMARY KEY,
    file_path      TEXT      NOT NULL,
    duration       INTEGER   NOT NULL,
    recording_date TIMESTAMP NOT NULL,
    format         TEXT      NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Store transcription segments
CREATE TABLE IF NOT EXISTS transcriptions
(
    segment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id TEXT  NOT NULL,
    speaker_id   TEXT  NOT NULL,
    start_time   FLOAT NOT NULL,
    end_time     FLOAT NOT NULL,
    text         TEXT  NOT NULL,
    confidence   FLOAT,
    FOREIGN KEY (recording_id) REFERENCES recordings (recording_id)
);

-- Store identified topics
CREATE TABLE IF NOT EXISTS topics
(
    topic_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id     TEXT NOT NULL,
    topic_name       TEXT NOT NULL,
    start_time       FLOAT,
    end_time         FLOAT,
    importance_score FLOAT,
    FOREIGN KEY (recording_id) REFERENCES recordings (recording_id)
);

-- Add Discussion Thread table
CREATE TABLE IF NOT EXISTS discussion_threads
(
    thread_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id        TEXT    NOT NULL,
    topic_id            INTEGER NOT NULL,
    initial_argument_id INTEGER,
    summary             TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recording_id) REFERENCES recordings (recording_id),
    FOREIGN KEY (topic_id) REFERENCES topics (topic_id)
);

-- Add Arguments table
CREATE TABLE IF NOT EXISTS arguments
(
    argument_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id     TEXT NOT NULL,
    thread_id        INTEGER,
    speaker_id       TEXT NOT NULL,
    timestamp        REAL NOT NULL,
    main_claim       TEXT NOT NULL,
    argument_type    TEXT NOT NULL,
    parent_id        INTEGER,
    confidence_score REAL      DEFAULT 1.0,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recording_id) REFERENCES recordings (recording_id),
    FOREIGN KEY (thread_id) REFERENCES discussion_threads (thread_id),
    FOREIGN KEY (parent_id) REFERENCES arguments (argument_id)
);

-- Add Supporting Points table
CREATE TABLE IF NOT EXISTS supporting_points
(
    point_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    argument_id      INTEGER NOT NULL,
    text             TEXT    NOT NULL,
    evidence         TEXT,
    confidence_score REAL DEFAULT 1.0,
    FOREIGN KEY (argument_id) REFERENCES arguments (argument_id)
);


-- Create indices for better query performance
CREATE INDEX IF NOT EXISTS idx_transcriptions_recording ON transcriptions (recording_id);
CREATE INDEX IF NOT EXISTS idx_topics_recording ON topics (recording_id);
CREATE INDEX IF NOT EXISTS idx_arguments_recording ON arguments (recording_id);
CREATE INDEX IF NOT EXISTS idx_arguments_topic ON arguments (topic_id);
