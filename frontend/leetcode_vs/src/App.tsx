import { useEffect, useState, type FormEvent } from 'react'
import './App.css'

type Topic = { name: string; slug: string }

type Filters = {
  difficulties: string[]
  topics: Topic[]
}

type Player = {
  player_id: number
  username: string
  score: number
  result: string
}

type Problem = {
  title: string
  slug: string
  url: string
  difficulty: string
  display_order: number
}

type Room = {
  room_code: string
  status: string
  start_time: string | null
  end_time: string | null
  players: Player[]
  problems: Problem[]
}

type Session = {
  username: string
  playerId: number | null
  roomCode: string | null
  hostId: number | null
}

const STORAGE_KEY = 'leetcode_vs'

const emptySession: Session = {
  username: '',
  playerId: null,
  roomCode: null,
  hostId: null,
}

function loadSession(): Session {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return emptySession
    return { ...emptySession, ...JSON.parse(saved) }
  } catch {
    return emptySession
  }
}

function saveSession(session: Session) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(readError(data))
  }
  return data as T
}

function readError(data: { detail?: unknown }): string {
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => (item && typeof item.msg === 'string' ? item.msg : 'Invalid value'))
      .join(' ')
  }
  return 'Request failed'
}

function timeLeft(endTime: string | null): string {
  if (!endTime) return ''
  const remaining = new Date(endTime).getTime() - Date.now()
  if (remaining <= 0) return '0:00'
  const totalSeconds = Math.floor(remaining / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

function App() {
  const [session, setSession] = useState<Session>(loadSession)
  const [room, setRoom] = useState<Room | null>(null)
  const [error, setError] = useState('')
  const [clock, setClock] = useState(timeLeft(null))

  function updateSession(next: Session) {
    setSession(next)
    saveSession(next)
  }

  useEffect(() => {
    if (!session.roomCode) return

    let cancelled = false

    async function loadRoom() {
      try {
        const next = await api<Room>(`/backend/rooms/${session.roomCode}`)
        if (!cancelled) {
          setRoom(next)
          setError('')
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load room')
      }
    }

    loadRoom()
    const poll = window.setInterval(loadRoom, 5000)
    return () => {
      cancelled = true
      window.clearInterval(poll)
    }
  }, [session.roomCode])

  useEffect(() => {
    if (!room?.end_time) return
    const tick = window.setInterval(() => setClock(timeLeft(room.end_time)), 1000)
    setClock(timeLeft(room.end_time))
    return () => window.clearInterval(tick)
  }, [room?.end_time])

  function leaveRoom() {
    setRoom(null)
    setError('')
    updateSession({ ...session, roomCode: null, playerId: null, hostId: null })
  }

  return (
    <main className="page">
      <header className="top">
        <h1>LeetCode Versus</h1>
        {session.roomCode && (
          <button type="button" onClick={leaveRoom}>
            Leave room
          </button>
        )}
      </header>

      {error && <p className="error">{error}</p>}

      {session.roomCode && room ? (
        <RoomView
          room={room}
          clock={clock}
          isHost={session.hostId !== null && session.playerId === session.hostId}
          playerId={session.playerId}
          onStart={async () => {
            if (session.playerId === null || !session.roomCode) return
            setError('')
            try {
              await api(`/backend/rooms/${session.roomCode}/start`, {
                method: 'POST',
                body: JSON.stringify({ player_id: session.playerId }),
              })
              const next = await api<Room>(`/backend/rooms/${session.roomCode}`)
              setRoom(next)
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Could not start room')
            }
          }}
        />
      ) : (
        <Home
          username={session.username}
          onUsername={(username) => updateSession({ ...session, username })}
          onEnter={(next) => {
            setError('')
            updateSession({ ...session, ...next })
          }}
          onError={setError}
        />
      )}
    </main>
  )
}

function Home({
  username,
  onUsername,
  onEnter,
  onError,
}: {
  username: string
  onUsername: (username: string) => void
  onEnter: (next: Pick<Session, 'username' | 'playerId' | 'roomCode' | 'hostId'>) => void
  onError: (message: string) => void
}) {
  const [filters, setFilters] = useState<Filters | null>(null)
  const [difficulty, setDifficulty] = useState('Easy')
  const [topic, setTopic] = useState('')
  const [duration, setDuration] = useState(30)
  const [problemCount, setProblemCount] = useState(3)
  const [roomCode, setRoomCode] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api<Filters>('/backend/filters')
      .then((next) => {
        setFilters(next)
        setDifficulty(next.difficulties[0] ?? 'Easy')
        setTopic(next.topics[0]?.name ?? '')
      })
      .catch((err) => onError(err instanceof Error ? err.message : 'Could not load filters'))
  }, [onError])

  async function createRoom(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    onError('')
    try {
      const created = await api<{ room_code: string; host_id: number }>('/backend/rooms/create', {
        method: 'POST',
        body: JSON.stringify({
          host_username: username,
          duration,
          problem_count: problemCount,
          difficulty,
          topics: [topic],
        }),
      })
      onEnter({
        username,
        playerId: created.host_id,
        roomCode: created.room_code,
        hostId: created.host_id,
      })
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Could not create room')
    } finally {
      setBusy(false)
    }
  }

  async function joinRoom(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    onError('')
    try {
      const joined = await api<{ room_code: string; player_id: number }>(
        `/backend/rooms/${roomCode.trim()}/join`,
        {
          method: 'POST',
          body: JSON.stringify({ username }),
        },
      )
      onEnter({
        username,
        playerId: joined.player_id,
        roomCode: joined.room_code,
        hostId: null,
      })
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Could not join room')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="home">
      <label>
        LeetCode username
        <input value={username} onChange={(event) => onUsername(event.target.value)} />
      </label>

      <form className="card" onSubmit={createRoom}>
        <h2>Create a room</h2>
        <label>
          Minutes
          <input
            type="number"
            min={1}
            max={180}
            value={duration}
            onChange={(event) => setDuration(Number(event.target.value))}
          />
        </label>
        <label>
          Problems
          <input
            type="number"
            min={1}
            max={10}
            value={problemCount}
            onChange={(event) => setProblemCount(Number(event.target.value))}
          />
        </label>
        <label>
          Difficulty
          <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
            {(filters?.difficulties ?? ['Easy', 'Medium', 'Hard']).map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label>
          Topic
          <select value={topic} onChange={(event) => setTopic(event.target.value)}>
            {(filters?.topics ?? []).map((item) => (
              <option key={item.slug} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={busy || !username || !topic}>
          Create
        </button>
      </form>

      <form className="card" onSubmit={joinRoom}>
        <h2>Join a room</h2>
        <label>
          Room code
          <input value={roomCode} onChange={(event) => setRoomCode(event.target.value.toUpperCase())} />
        </label>
        <button type="submit" disabled={busy || !username || !roomCode.trim()}>
          Join
        </button>
      </form>
    </div>
  )
}

function RoomView({
  room,
  clock,
  isHost,
  playerId,
  onStart,
}: {
  room: Room
  clock: string
  isHost: boolean
  playerId: number | null
  onStart: () => void
}) {
  return (
    <section className="room">
      <p className="code">{room.room_code}</p>
      <p>
        {room.status}
        {room.status === 'Active' && clock ? ` · ${clock}` : ''}
      </p>

      {room.status === 'Created' && isHost && (
        <button type="button" onClick={onStart}>
          Start match
        </button>
      )}
      {room.status === 'Created' && !isHost && <p>Waiting for the host to start.</p>}
      {room.status === 'Inactive' && <p>This lobby expired before it started.</p>}

      <h2>Problems</h2>
      <ul>
        {room.problems.map((problem) => (
          <li key={problem.slug}>
            <a href={problem.url} target="_blank" rel="noreferrer">
              {problem.title}
            </a>
            <span>{problem.difficulty}</span>
          </li>
        ))}
      </ul>

      <h2>Scoreboard</h2>
      <ul>
        {room.players.map((player) => (
          <li key={player.player_id} className={player.result === 'Winner' ? 'winner' : ''}>
            <span>
              {player.username}
              {player.player_id === playerId ? ' (you)' : ''}
            </span>
            <span>
              {player.score} · {player.result}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default App
