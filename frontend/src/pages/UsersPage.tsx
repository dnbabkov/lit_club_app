import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { getPublicUsers, getUsers, type UserPublicRead, type UserRead, type UserAdminRead } from "../api/auth"
import { useAuth } from "../auth/useAuth"
import { Layout } from "../components/Layout"
import { UserEditor } from "../components/UserEditor"

function formatTelegramLogin(login: string | null): string {
  return !login ? "Не указан" : login.startsWith("@") ? login : `@${login}`
}

function getRoleLabel(role: UserRead["role"]): string {
  return role === "admin" ? "Админ" : role === "moderator" ? "Модератор" : "Участник"
}

export function UsersPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const isAdmin = user?.role === "admin"
  const [users, setUsers] = useState<(UserAdminRead | UserPublicRead)[]>([])
  const [editor, setEditor] = useState<{ user: UserAdminRead | null } | null>(null)
  const [success, setSuccess] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")

  useEffect(() => {
    let active = true
    const request = isAdmin ? getUsers() : getPublicUsers()
    request.then(
      users => {
        if (!active) return
        setUsers(users)
        setErrorMessage("")
        setIsLoading(false)
      },
      error => {
        if (!active) return
        setErrorMessage(error instanceof Error ? error.message : "Не удалось загрузить пользователей")
        setIsLoading(false)
      },
    )
    return () => { active = false }
  }, [isAdmin])

  function openUserProfile(username: string) {
    navigate(`/users/${encodeURIComponent(username)}/profile`)
  }

  const cellStyle = { borderBottom: "1px solid #eee", padding: 8, textAlign: "left" as const }
  return (
    <Layout>
      <h1>Пользователи</h1>
      {isAdmin && !editor && <button type="button" aria-label="Добавить пользователя" onClick={() => { setSuccess(""); setEditor({ user: null }) }}>＋ Добавить пользователя</button>}
      {isAdmin && editor && <UserEditor user={editor.user} onClose={() => setEditor(null)} onSaved={saved => {
        setUsers(previous => [...previous.filter(item => item.id !== saved.id), saved].sort((a, b) => a.username.localeCompare(b.username)))
        setEditor(null)
        setSuccess("Пользователь сохранён")
      }} />}
      {success && <p role="status">{success}</p>}
      {isLoading && <p>Загрузка...</p>}
      {!isLoading && errorMessage && <p style={{ color: "crimson" }}>{errorMessage}</p>}
      {!isLoading && !errorMessage && users.length === 0 && <p>Пользователи не найдены.</p>}
      {!isLoading && !errorMessage && users.length > 0 && (
        isAdmin ? (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 16 }}>
              <thead><tr>{["Имя", "Тег", "Telegram ID", "Роль", "Действия"].map(label => <th key={label} style={cellStyle}>{label}</th>)}</tr></thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.id}>
                    <td style={cellStyle}>{user.username}</td>
                    <td style={cellStyle}>{"telegram_login" in user ? formatTelegramLogin(user.telegram_login) : "Не указан"}</td>
                    <td style={cellStyle}>{"tg_id" in user ? user.tg_id ?? "Не привязан" : "Не привязан"}</td>
                    <td style={cellStyle}>{"role" in user ? getRoleLabel(user.role) : "Участник"}</td>
                    <td style={cellStyle}>
                      <button type="button" onClick={() => openUserProfile(user.username)}>Перейти в профиль</button>
                      {"tg_id" in user && <button type="button" disabled={editor !== null} onClick={() => { setSuccess(""); setEditor({ user }) }}>Редактировать</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 16 }}>
            {users.map(user => (
              <div key={user.id} style={{ display: "flex", alignItems: "center", gap: 12, border: "1px solid #ddd", borderRadius: 8, padding: 12, textAlign: "left" }}>
                <div aria-hidden="true" style={{ width: 40, height: 40, borderRadius: "50%", border: "1px solid #ddd", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 600, flexShrink: 0 }}>
                  {user.username.trim().charAt(0).toUpperCase() || "?"}
                </div>
                <strong style={{ flex: 1, minWidth: 0, overflowWrap: "anywhere" }}>{user.username}</strong>
                <span aria-hidden="true">—</span>
                <button type="button" onClick={() => openUserProfile(user.username)}>Перейти в профиль</button>
              </div>
            ))}
          </div>
        )
      )}
    </Layout>
  )
}
