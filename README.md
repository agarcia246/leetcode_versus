# LeetCode Versus

Timed head-to-head LeetCode matches. A host picks a duration, a difficulty, a topic, and how many problems to play. Friends join with a 6-letter room code, solve on leetcode.com, and this app scores the match from each player's public submissions.

One Python process serves the API and the built page. SQLite lives at `data/app.db`.

## Run it

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Open http://127.0.0.1:8000.

The process binds to `0.0.0.0` and reads `PORT` (default `8000`). The database directory is `DATA_DIR` (default `data`, resolved from the repository root). A `.env` file is optional. The app starts without one.

| Variable | Default | What it does |
|---|---|---|
| `HOST` | `0.0.0.0` | Address the process binds to |
| `PORT` | `8000` | Port |
| `DATA_DIR` | `data` | Directory for `app.db` |

LeetCode's public GraphQL API has to be reachable. A player only scores if that LeetCode profile exposes recent submissions.

## Rebuild the page

The page already built into `app/static` is what `python -m app.main` serves. Rebuild only if you change `frontend/leetcode_vs`:

```bash
cd frontend/leetcode_vs
npm install
npm run build
```

Vite writes the bundle back to `app/static`. The dev server proxies `/backend` to port 8000:

```bash
python -m app.main
cd frontend/leetcode_vs && npm run dev
```

## Tests and coverage

From the repository root, with the virtualenv active:

```bash
python -m pytest --cov=app.domain.backend.services --cov-report=term-missing
```

Result: 100% coverage of `app/domain/backend/services.py` (418 statements).

## API

| Method | Path | What it does |
|---|---|---|
| `GET` | `/` | The match page |
| `GET` | `/backend/filters` | Difficulties and LeetCode topic tags |
| `POST` | `/backend/rooms/create` | Create a lobby and pick problems |
| `POST` | `/backend/rooms/{room_code}/join` | Join with a LeetCode username |
| `POST` | `/backend/rooms/{room_code}/start` | Host starts the clock |
| `GET` | `/backend/rooms/{room_code}` | Room state. While the match is live this also polls LeetCode |

Other write-ups: `REPORT.md`, `ADR.md`, `AI_USAGE.md`.
