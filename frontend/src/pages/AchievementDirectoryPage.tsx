import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { getAchievementDirectory } from "../api/achievements"
import type { UserPublicRead } from "../api/auth"
import { useAuth } from "../auth/useAuth"
import { Layout } from "../components/Layout"

const usernameCollator = new Intl.Collator("ru", { sensitivity: "base" })

export function AchievementDirectoryPage() {
  const navigate = useNavigate()
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState<UserPublicRead[] | null>(null)
  const [error, setError] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const [search, setSearch] = useState("")

  useEffect(() => {
    let active = true
    getAchievementDirectory().then(
      data => { if (active) setUsers(data.filter(user => user.username !== "dev_admin")) },
      () => { if (active) setError(true) },
    )
    return () => { active = false }
  }, [attempt])

  const cleanSearch = search.trim().toLocaleLowerCase("ru")
  const selfUser = currentUser?.username === "dev_admin" ? null : currentUser
  const directoryUsers = users && selfUser && !users.some(user => user.id === selfUser.id)
    ? [{ id: selfUser.id, username: selfUser.username }, ...users]
    : users
  const orderedUsers = directoryUsers ? [...directoryUsers]
    .filter(user => !cleanSearch || user.username.toLocaleLowerCase("ru").includes(cleanSearch))
    .sort((left, right) => {
    if (left.id === right.id) return 0
    if (left.id === currentUser?.id) return -1
    if (right.id === currentUser?.id) return 1
    return usernameCollator.compare(left.username, right.username) || left.id - right.id
  }) : []

  function openAchievements(user: UserPublicRead) {
    const path = user.id === currentUser?.id
      ? "/profile/achievements"
      : `/users/${encodeURIComponent(user.username)}/profile/achievements`
    navigate(path, { state: { from: "achievement-directory" } })
  }

  return <Layout>
    <h1>Ачивки</h1>
    <label style={{ display: "block", maxWidth: 480, marginTop: 16 }}>Поиск по людям
      <input value={search} onChange={event => setSearch(event.target.value)} placeholder="Начните вводить имя" style={{ display: "block", width: "100%", boxSizing: "border-box", marginTop: 6 }} />
    </label>
    {error ? (
      <div role="alert">
        <p>Не удалось загрузить каталог ачивок.</p>
        <button type="button" onClick={() => { setUsers(null); setError(false); setAttempt(value => value + 1) }}>Повторить</button>
      </div>
    ) : users === null ? (
      <p role="status">Загрузка пользователей…</p>
    ) : users.length === 0 ? (
      <p>Пользователи не найдены.</p>
    ) : orderedUsers.length === 0 ? (
      <p>По этому запросу никого не найдено.</p>
    ) : (
      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 16 }}>
        {orderedUsers.map(user => (
          <div key={user.id} style={{ display: "flex", alignItems: "center", gap: 12, border: "1px solid #ddd", borderRadius: 8, padding: 12, textAlign: "left" }}>
            <div aria-hidden="true" style={{ width: 40, height: 40, borderRadius: "50%", border: "1px solid #ddd", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 600, flexShrink: 0 }}>
              {user.username.trim().charAt(0).toUpperCase() || "?"}
            </div>
            <strong style={{ flex: 1, minWidth: 0, overflowWrap: "anywhere" }}>{user.username}{user.id === currentUser?.id ? " (я)" : ""}</strong>
            <button type="button" onClick={() => openAchievements(user)}>Посмотреть ачивки</button>
          </div>
        ))}
      </div>
    )}
  </Layout>
}
