PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lc_user TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    lc_id TEXT NOT NULL UNIQUE,
    lc_url TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard'))
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL UNIQUE,
    host_id INTEGER NOT NULL REFERENCES players(id),
    current_status TEXT NOT NULL DEFAULT 'Created' CHECK (current_status IN ('Created', 'Active', 'Inactive', 'Finished')),
    duration_min INTEGER NOT NULL DEFAULT 30,
    creation_time TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    last_polled_at TEXT,
    poll_error TEXT
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    problem_id INTEGER NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    submitted_at TEXT NOT NULL,
    current_status TEXT NOT NULL CHECK (current_status IN ('Accepted', 'Wrong_Answer', 'Time_Limit', 'Pending'))
);

CREATE TABLE IF NOT EXISTS room_problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    problem_id INTEGER NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    display_order INTEGER NOT NULL,
    UNIQUE (room_id, problem_id),
    UNIQUE (room_id, display_order)
);

CREATE TABLE IF NOT EXISTS room_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    joined_at TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    result TEXT NOT NULL DEFAULT 'Created' CHECK (result IN ('Created', 'In_Progress', 'Winner', 'Loser')),
    UNIQUE (room_id, player_id)
);

CREATE TABLE IF NOT EXISTS problem_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id INTEGER NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    UNIQUE (problem_id, topic_id)
);
