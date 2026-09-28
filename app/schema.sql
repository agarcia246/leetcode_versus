CREATE TABLE Room (
    id INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,

    room_code TEXT NOT NULL UNIQUE,
    host_id INTEGER NOT NULL REFERENCES Players(id),
    current_status TEXT NOT NULL,
    duration_min INTEGER NOT NULL DEFAULT 30,
    creation_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    start_time TEXT,
    end_time TEXT,

    last_polled_at TEXT
    poll_error TEXT
);


CREATE TABLE Players (
    id INTEGER PRIMARY KEY UNIQUE AUTOINCREMENT,
    leetcode_user TEXT NOT NULL

);

