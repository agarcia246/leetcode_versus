CREATE TABLE Rooms (
    id INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL UNIQUE,
    host_id INTEGER NOT NULL REFERENCES Players(id),
    current_status TEXT NOT NULL DEFAULT "Created" CHECK(current_status IN ("Created", "Active", "Inactive", "Finished")),
    duration_min INTEGER NOT NULL DEFAULT 30,
    creation_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    start_time TEXT,
    end_time TEXT,
    last_polled_at TEXT,
    poll_error TEXT,
);


CREATE TABLE Players (
    id INTEGER PRIMARY KEY UNIQUE AUTOINCREMENT,
    lc_user TEXT NOT NULL UNIQUE,

);


CREATE TABLE Problems (
    id INTEGER PRIMARY KEY UNIQUE AUTOINCREMENT,
    title TEXT NOT NULL,
    lc_id TEXT NOT NULL UNIQUE,
    lc_url TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK(difficulty IN ("Easy","Medium","Hard")),
);



CREATE TABLE Submissions (
    id INTEGER PRIMARY KEY UNIQUE AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES Rooms(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES Players(id) ON DELETE CASCADE,
    problem_id INTEGER NOT NULL REFERENCES Problems(id) ON DELETE CASCADE,
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    current_status TEXT NOT NULL CHECK(current_status IN ("Accepted", "Wrong_Answer", "Time_Limit", "Pending"))
);

CREATE TABLE Topics (
    id INTEGER PRIMARY KEY UNIQUE AUTOINCREMENT,
    topic_name TEXT NOT NULL UNIQUE,
);







CREATE TABLE Room_Problems (
    id INTEGER PRIMARY KEY UNIQUE AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES Rooms(id) ON DELETE CASCADE,
    problem_id INTEGER NOT NULL REFERENCES Problems(id) ON DELETE CASCADE,
    display_order INTEGER NOT NULL,

    UNIQUE(room_id, problem_id),
    UNIQUE(room_id, display_order)
);


CREATE TABLE Room_Players (
    id INTEGER PRIMARY KEY UNIQUE AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES Rooms(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES Players(id) ON DELETE CASCADE,
    joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    score INTEGER NOT NULL DEFAULT 0,
    result TEXT NOT NULL DEFAULT "Created" CHECK( result IN ("Created","In_Progress", "Winner", "Loser")),

    UNIQUE(room_id, player_id)
);



CREATE TABLE Problem_Topics (
    id INTEGER PRIMARY KEY UNIQUE AUTOINCREMENT,
    problem_id INTEGER NOT NULL REFERENCES Problems(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES Topics(id) ON DELETE CASCADE,

    UNIQUE(problem_id, topic_id)
);


