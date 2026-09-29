import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { updateCurrentUser, type UserRead } from "../api/auth"
import { getMyProfile, getUserProfile } from "../api/profile"
import { useAuth } from "../auth/useAuth"
import { Layout } from "../components/Layout"
import { ProfileBookCard } from "../components/profile/ProfileBookCard"
import type { UserProfileRead } from "../types/profile"

function getRoleLabel(role: UserProfileRead["role"]): string {
  return role === "admin" ? "Администратор" : role === "moderator" ? "Модератор" : "Участник"
}

function UsernameEditor({ profile, onUpdated }: { profile: UserProfileRead, onUpdated: (user: UserRead) => void }) {
  const [usernameDraft, setUsernameDraft] = useState(profile.username)
  const [usernameSaving, setUsernameSaving] = useState(false)
  const [usernameMessage, setUsernameMessage] = useState("")
  const [usernameError, setUsernameError] = useState("")

  async function saveUsername() {
    const cleanUsername = usernameDraft.trim()
    if (!cleanUsername) {
      setUsernameError("Введите имя.")
      return
    }
    setUsernameSaving(true)
    setUsernameError("")
    setUsernameMessage("")
    try {
      const updatedUser = await updateCurrentUser({ username: cleanUsername })
      setUsernameDraft(updatedUser.username)
      setUsernameMessage("Имя обновлено.")
      onUpdated(updatedUser)
    } catch (error) {
      setUsernameError(error instanceof Error ? error.message : "Не удалось обновить имя")
    } finally {
      setUsernameSaving(false)
    }
  }

  return <div style={{ display: "grid", gap: 8, maxWidth: 360, marginTop: 16 }}>
    <label>Имя
      <input value={usernameDraft} maxLength={50} onChange={event => {
        setUsernameDraft(event.target.value)
        setUsernameError("")
        setUsernameMessage("")
      }} />
    </label>
    {usernameError && <p role="alert" style={{ margin: 0 }}>{usernameError}</p>}
    {usernameMessage && <p role="status" style={{ margin: 0 }}>{usernameMessage}</p>}
    <button type="button" onClick={() => void saveUsername()} disabled={usernameSaving || usernameDraft.trim() === profile.username}>
      {usernameSaving ? "Сохранение…" : "Сохранить имя"}
    </button>
  </div>
}

export function ProfilePage() {
  const { username } = useParams<{ username: string }>()
  const navigate = useNavigate()
  const { user: currentUser, updateUser } = useAuth()
  const isOwnProfileRoute = !username
  const [result, setResult] = useState<{
    username?: string
    profile: UserProfileRead | null
    error: string
  } | null>(null)
  const current = result?.username === username ? result : null
  const profile = current?.profile

  useEffect(() => {
    let active = true
    const request = username ? getUserProfile(username) : getMyProfile()
    request.then(
      profile => { if (active) setResult({ username, profile, error: "" }) },
      error => { if (active) setResult({ username, profile: null, error: error instanceof Error ? error.message : "Не удалось загрузить профиль" }) },
    )
    return () => { active = false }
  }, [username])

  useEffect(() => {
    if (username && profile && profile.id === currentUser?.id) {
      navigate("/profile", { replace: true })
    }
  }, [currentUser, navigate, profile, username])

  return (
    <Layout>
      <h1>{isOwnProfileRoute ? "Профиль" : "Профиль пользователя"}</h1>
      {!current && <p>Загрузка...</p>}
      {current?.error && <p style={{ color: "crimson" }}>{current.error}</p>}
      {profile && (
        <>
          <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, marginBottom: 24 }}>
            <h2 style={{ marginTop: 0, marginBottom: 12 }}>{profile.username}</h2>
            {isOwnProfileRoute && (
              <p style={{ margin: "4px 0" }}><strong>Telegram login:</strong> {profile.telegram_login ?? "Не указан"}</p>
            )}
            <p style={{ margin: "4px 0" }}><strong>Роль:</strong> {getRoleLabel(profile.role)}</p>
            {isOwnProfileRoute && <UsernameEditor key={profile.id} profile={profile} onUpdated={user => {
              updateUser(user)
              setResult(previous => previous?.profile
                ? { ...previous, profile: { ...previous.profile, username: user.username } }
                : previous)
            }} />}
            <button type="button" style={{ marginTop: 16 }} onClick={() => navigate(
              isOwnProfileRoute ? "/profile/achievements" : `/users/${encodeURIComponent(profile.username)}/profile/achievements`
            )}>Достижения</button>
          </div>
          <div>
            <h2>Предложенные книги</h2>
            {profile.nominated_books.length === 0 ? (
              <p>{isOwnProfileRoute ? "Вы пока не предлагали ни одной книги." : "Пользователь пока не предлагал ни одной книги."}</p>
            ) : profile.nominated_books.map(item => <ProfileBookCard key={item.book_id} item={item} />)}
          </div>
        </>
      )}
    </Layout>
  )
}
