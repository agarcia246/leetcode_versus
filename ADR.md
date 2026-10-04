# Architecture Decision Record

Five decisions. Rewrite every **YOU FILL** block in your own words before you submit. The written check grades these against what you can explain, not against how finished the draft looks.

Dates below are the commit dates where that decision shows up in git. Change a date if you actually decided earlier or later. The five dates still have to cover at least three different calendar days.

## [1]. Backend language and framework

Date: 2026-09-28
Status: Decided
Context: The app is a small JSON API plus a page, one process, SQLite, and a call out to LeetCode. I already use Python and React.
Decision: FastAPI for the API, with request bodies checked by Pydantic models in `app/domain/backend/models.py`. The React app is built with Vite into `app/static` and served by the same process (`app/main.py`, `app/domain/frontend/router.py`).

> **YOU FILL.** Name one real alternative you rejected and why. The brief expects this to be Flask or Django if you considered them, or server-rendered templates if the alternative was about the page. Your 28 Sep notes only say React because you already know it and can build quickly. Keep that if it is the real reason, and add what you rejected:
>
> Alternatives considered: `[[FILL]]`

Consequences: One `requirements.txt` and one start command (`python -m app.main`) fit the single-container contract. The React source still has its own `frontend/leetcode_vs/package.json`, which is a second manifest the brief does not want. The running app does not need that folder if `app/static` is already built.

## [2]. Two feature domains that can be split later

Date: 2026-09-30
Status: Decided
Context: The match and the problem list are different jobs. The assignment wants both in one process now, with a seam I can point at later.
Decision: Domain 1 is the match: `rooms`, `players`, `room_players`, and the lifecycle in `create_room`, `join_room`, `start_room`, `expire_inactive_lobby`, and `assign_match_results`. Domain 2 is the catalog and the solves: `problems`, `topics`, `problem_topics`, `room_problems`, `submissions`, plus `fetch_problems_for_topics`, `upsert_problem`, and `record_match_submissions`. They meet at `room_problems` and at those two function calls. Both live in `app/domain/backend/services.py` today. `app/domain/frontend` only returns the built page.

> **YOU FILL.** Confirm this split is how you think about it. If you meant a different pair of domains, replace the Decision paragraph.
>
> Alternatives considered: `[[FILL: what else you considered, for example one undifferentiated CRUD module, or two Python packages from the start, and why you rejected that]]`

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

> **YOU FILL** if this is the wrong "thing I chose not to build." Other real candidates in the repo: a hand-filled problem bank (`todo.md` still says to fill `problems`, `topics`, and `problem_topics`; the app fetches from LeetCode instead), and chat or spectator mode. If you swap the decision, keep the date on a day you actually made it.

Consequences: Scoring fails closed when LeetCode hides a profile. `get_room` stores that on `rooms.poll_error` and still returns the room. The client can be a few seconds behind a solve because it polls instead of receiving a push.
