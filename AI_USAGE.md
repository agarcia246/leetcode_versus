# AI usage log

Tools:

- **Nebula One** (https://nebulaone.ie.edu/chat/projects/1637cac5-53e3-4702-8bca-88e34df392bb).
- **Cursor** on last 4 commits.

The last column is empty on purpose. The brief says that cell is in your own words, using your real function and variable names. Paste the prompt you actually sent. If you only asked a question and wrote the code yourself, disposition is **Rejected**. If you kept the answer but changed it, **Modified**. If you kept it as given, **Accepted**.

Rows follow the commits. Split a row if one commit was several different chats. Delete a row you did not actually use a tool for.

| Date/commit | Tool | Prompt | Disposition (Accepted/Modified/Rejected) | What changed & why (if modified) | In my own words, how this works |
|---|---|---|---|---|---|
| 2026-09-28 `52b3265` | Nebula One | [[FILL: paste the question. This commit is the idea, the first ADR notes, and `Research/Database.png`.]] | [[FILL]] | Repo started as a LeetCode head-to-head idea. Notes name React, FastAPI, SQLite, and the LeetCode GraphQL API. | [[FILL]] |
| 2026-09-29 `666bf51`, `1cd62ec` | Nebula One | [[FILL: paste the schema question.]] | [[FILL]] | `app/schema.sql`: `players`, `topics`, `problems`, `rooms`, `submissions`, `room_problems`, `room_players`, `problem_topics`. ADR entry on the join table vs storing topics as a string. | [[FILL: how `problem_topics` relates a problem to a topic, in your words]] |
| 2026-09-30 `d5d8ca1` | Nebula One | [[FILL]] | [[FILL]] | Package layout: `app/main.py`, `app/database.py`, `app/domain/backend/`, `app/domain/frontend/`. | [[FILL]] |
| 2026-10-01 `d4443e6` | Nebula One | [[FILL]] | [[FILL]] | SQLAlchemy models and the first router stubs in `app/domain/backend/models.py` and `router.py`. Vite app created under `frontend/leetcode_vs`. | [[FILL: what `CreateRoomModel` checks before a room is stored]] |
| 2026-10-03 `57c9a54` | Nebula One | [[FILL]] | [[FILL]] | Room creation path started in `app/domain/backend/services.py`, with `app/database.py` and `app/main.py`. | [[FILL]] |
| 2026-10-04 `9b2f6a5` | [[FILL: Nebula One or Cursor]] | [[FILL]] | [[FILL]] | Most of the service functions except `get_room`. `notepad.py` is a scratch call to `recentSubmissionList` for one username. | [[FILL: what `generate_room_code` does, and what `lookup_leetcode_user` returns]] |
| 2026-10-04 `f67f69b` | [[FILL: Nebula One or Cursor]] | [[FILL]] | [[FILL]] | `services.py` filled out, including problem fetch and submission recording. | [[FILL: walk `record_match_submissions`. When does `room_player.score` go up?]] |
| 2026-10-04 `1a77ba4` | Cursor | [[FILL: paste the error you asked Cursor to fix]] | [[FILL]] | Commit message: used Cursor to fix errors in `services.py`, `models.py`, and `router.py`. | [[FILL: what was broken, and what the fix does]] |
| 2026-10-04 `3c55177` | Cursor | [[FILL]] | [[FILL]] | Backend API finished. `app/config.py` reads `HOST`, `PORT`, and `DATA_DIR`. `init_db` applies `schema.sql`. Routers: `GET /backend/filters`, `POST /backend/rooms/create`, `POST /backend/rooms/{room_code}/join`, `POST /backend/rooms/{room_code}/start`, `GET /backend/rooms/{room_code}`. | [[FILL: what `get_room` does on each poll, including `assign_match_results`]] |
| 2026-10-04 `c0d8a5c` | Cursor | [[FILL]] | [[FILL]] | React page in `frontend/leetcode_vs/src/App.tsx`. Vite `base` is `/static/` and the build output is `app/static`. The page stores `username`, `playerId`, `roomCode`, and `hostId` in `localStorage` under `leetcode_vs`, and calls `GET /backend/rooms/{code}` every 5 seconds. | [[FILL: what `createRoom` sends, and how the host start button is shown]] |

`d5fc0d7` (2 Oct, "some changes") only touched `assignment_1.md`. Leave it out unless a chat drove it.

`09a3c5c` is the merge of `features/api` into `main`. It is not its own AI session unless you used a tool to do the merge.
