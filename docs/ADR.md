# Architecture Decision Record


## [1]. Backend language and framework

Date: 2026-09-28

Status: Decided

Context: I am building a small app where users compete in LeetCode challenges against each other. The assignment requires SQLite and one process.

Decision: FastAPI for the API, SQLAlchemy for the SQLite models, and Pydantic models for the request bodies. The React page is built ahead of time and served by the same process from `app/static`.

Alternatives considered: While selecting this, I considered using Django and flask. I decided against both of these because I just needed to implement an api not a full web framework and because of this, fastapi was the most logical choice.

Consequences: the whole project falls under the single container requirement. Only one file is being run, which is the main.py file. Since the API is serving the react frontend we build this before and we keep the static files in app/static

## [2]. Two feature domains that can be split later

Date: 2026-09-30
Status: Decided
Context: The match and the problem list are different jobs. The assignment wants both in one process now, with a seam I can point at later.

Decision: Domain 1 is the match: `rooms`, `players`, `room_players`, and `create_room`, `join_room`, `start_room`, `expire_inactive_lobby`, and `assign_match_results`. Domain 2 is the catalog and the solves: `problems`, `topics`, `problem_topics`, `room_problems`, `submissions`, plus `fetch_problems_for_topics`, `upsert_problem`, and `record_match_submissions`. They meet at `room_problems`. Both live in `app/domain/backend/services.py` for now.

Alternatives considered: One CRUD module with no seam, or two Python packages from the start. I rejected two packages because this assignment is one process and the seam is only those calls. I rejected one blob because a later assignment has to split the domains.

Consequences: A later split can lift the catalog out behind `add_problems_to_room` and the submission polling inside `get_room` without rewriting the room-code, host, and score rules. Until then, one SQLite file and one module keep the deployment contract.

## [3]. SQLite schema: topics in a join table


Date: 2026-09-29

Status: Decided

Context: I started from the data. A match needs a room, the people in it, the problems they are racing, and the solves that count. Topics are shared by a lot of problems.

Decision: `rooms` is the center. `players`, `problems`, `submissions`, and `topics` hang off it. Many-to-many links are `room_players`, `room_problems`, and `problem_topics`. Topic names are not stored as one string on `problems`.

Alternatives considered: Drop `problem_topics` and store topics as a long string on `problems`. I rejected that because the same topics show up on many problems, so the names would be copied over and over, and filtering a room by topic would mean parsing that string.

Consequences: The API can be written against a stable shape. `upsert_problem` writes one row per problem and one `problem_topics` row per tag. This is the diagram in the report and in `app/schema.sql`.

## [4]. Testing approach


Date: 2026-10-04

Status: Decided

Context: The grade is on the match rules and the scoring rules, not on FastAPI routes. LeetCode cannot be a dependency of the test run.

Decision: pytest covers `app/domain/backend/services.py`. Room settings, the lobby clock, win/loss, and `record_match_submissions` are called directly. `leetcode_graphql` and `requests.post` are mocked. The measured result is 100% of that module.

Alternatives considered: Hitting the live LeetCode API from pytest, or only testing the routers. I rejected the live calls because they fail offline and depend on a public profile, and the routers are thin wrappers around the service functions.

Consequences: A change to who scores, or to when a lobby expires, fails in `tests/` without a network call. The React page is not part of this number.

## [5]. No in-app editor and no accounts

Date: 2026-10-04

Status: Decided

Context: A match is scored from LeetCode, not from code this app runs. Hosting an editor would mean running other people's code. A password account would duplicate the LeetCode username the score already depends on.

Decision: Players solve on leetcode.com. This app checks that the username exists (`lookup_leetcode_user`), shows problem links, and polls public submissions from `get_room`. Identity is the LeetCode username stored on `players.lc_user`. The page in `frontend/leetcode_vs/src/App.tsx` refreshes the room every 5 seconds. There is no WebSocket and no login.

Alternatives considered: An in-app editor, or pushing score updates over WebSockets instead of the 5-second poll. I rejected both because they add a second product (code execution, or a live channel) that the single process does not need in order to score a match.

Consequences: Scoring fails closed when LeetCode hides a profile. `get_room` stores that on `rooms.poll_error` and still returns the room. The client can be a few seconds behind a solve because it polls instead of receiving a push.
