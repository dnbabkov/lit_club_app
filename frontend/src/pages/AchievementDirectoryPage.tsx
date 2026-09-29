import { useEffect, useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { createAchievement, getAchievementDirectory } from "../api/achievements"
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
  const [formOpen, setFormOpen] = useState(false)
  const [recipientId, setRecipientId] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [image, setImage] = useState<File | null>(null)
  const [formError, setFormError] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState<{ id: number, recipient: UserPublicRead } | null>(null)

  useEffect(() => {
    let active = true
    getAchievementDirectory().then(
      data => { if (active) setUsers(data.filter(user => user.username !== "dev_admin")) },
      () => { if (active) setError(true) },
    )
    return () => { active = false }
  }, [attempt])

  const orderedUsers = users ? [...users].sort((left, right) => {
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

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const cleanTitle = title.trim()
    const cleanDescription = description.trim()
    if (!recipientId || !cleanTitle || !cleanDescription || !image) {
      setFormError("Заполните получателя, название, описание и выберите изображение.")
      return
    }
    if (cleanTitle.length > 200 || cleanDescription.length > 5000) {
      setFormError("Название должно быть не длиннее 200, а описание — 5000 символов.")
      return
    }
    const recipient = users?.find(user => user.id === Number(recipientId))
    if (!recipient || !currentUser) return
    setSubmitting(true)
    setFormError("")
    try {
      const achievement = await createAchievement(recipient.id, cleanTitle, cleanDescription, image)
      setRecipientId(""); setTitle(""); setDescription(""); setImage(null)
      setFormOpen(false)
      setSuccess({ id: achievement.id, recipient })
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Не удалось выдать ачивку")
    } finally {
      setSubmitting(false)
    }
  }

  return <Layout>
    <h1>Ачивки</h1>
    <button type="button" onClick={() => { setFormOpen(value => !value); setFormError(""); setSuccess(null) }}>
      Выдать ачивку
    </button>
    {formOpen && users !== null && <form onSubmit={submit} style={{ display: "grid", gap: 10, maxWidth: 600, marginTop: 16 }}>
      <label>Получатель
        <select required value={recipientId} onChange={event => setRecipientId(event.target.value)}>
          <option value="">Выберите пользователя</option>
          {users.map(user => <option key={user.id} value={user.id}>{user.username}</option>)}
        </select>
      </label>
      <label>Название
        <input required maxLength={200} value={title} onChange={event => setTitle(event.target.value)} />
      </label>
      <label>Описание
        <textarea required maxLength={5000} value={description} onChange={event => setDescription(event.target.value)} />
      </label>
      <label>Изображение
        <input required type="file" accept="image/png,image/jpeg,image/webp" onChange={event => setImage(event.target.files?.[0] ?? null)} />
      </label>
      {formError && <p role="alert">{formError}</p>}
      <button type="submit" disabled={submitting}>{submitting ? "Выдача…" : "Выдать ачивку"}</button>
    </form>}
    {success && <p role="status">Ачивка выдана. <button type="button" onClick={() => openAchievements(success.recipient)}>Открыть достижения пользователя</button></p>}
    {error ? (
      <div role="alert">
        <p>Не удалось загрузить каталог ачивок.</p>
        <button type="button" onClick={() => { setUsers(null); setError(false); setAttempt(value => value + 1) }}>Повторить</button>
      </div>
    ) : users === null ? (
      <p role="status">Загрузка пользователей…</p>
    ) : users.length === 0 ? (
      <p>Пользователи не найдены.</p>
    ) : (
      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 16 }}>
        {orderedUsers.map(user => (
          <div key={user.id} style={{ display: "flex", alignItems: "center", gap: 12, border: "1px solid #ddd", borderRadius: 8, padding: 12, textAlign: "left" }}>
            <div aria-hidden="true" style={{ width: 40, height: 40, borderRadius: "50%", border: "1px solid #ddd", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 600, flexShrink: 0 }}>
              {user.username.trim().charAt(0).toUpperCase() || "?"}
            </div>
            <strong style={{ flex: 1, minWidth: 0, overflowWrap: "anywhere" }}>{user.username}</strong>
            <button type="button" onClick={() => openAchievements(user)}>Посмотреть ачивки</button>
          </div>
        ))}
      </div>
    )}
  </Layout>
}
