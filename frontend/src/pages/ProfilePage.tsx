import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { getMyProfile, getUserProfile } from "../api/profile"
import { useAuth } from "../auth/useAuth"
import { Layout } from "../components/Layout"
import { ProfileBookCard } from "../components/profile/ProfileBookCard"
import type { UserProfileRead } from "../types/profile"

function getRoleLabel(role: UserProfileRead["role"]): string {
  return role === "admin" ? "Администратор" : role === "moderator" ? "Модератор" : "Участник"
}

export function ProfilePage() {
  const { username } = useParams<{ username: string }>()
  const navigate = useNavigate()
  const { user: currentUser } = useAuth()
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
