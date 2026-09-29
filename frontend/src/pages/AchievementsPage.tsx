import { useEffect, useState, type FormEvent } from "react"
import { useLocation, useNavigate, useParams } from "react-router-dom"
import { createAchievement } from "../api/achievements"
import { getMyProfile, getUserProfile } from "../api/profile"
import { useAuth } from "../auth/useAuth"
import { Layout } from "../components/Layout"
import { ProfileAchievements } from "../components/profile/ProfileAchievements"
import type { UserProfileRead } from "../types/profile"

export function AchievementsPage() {
  const { username } = useParams<{ username: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const { user: currentUser } = useAuth()
  const [recipientResult, setRecipientResult] = useState<{
    username?: string
    profile: UserProfileRead | null
    error: string
  } | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [image, setImage] = useState<File | null>(null)
  const [formError, setFormError] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [refreshAttempt, setRefreshAttempt] = useState(0)
  const profilePath = username ? `/users/${encodeURIComponent(username)}/profile` : "/profile"
  const backPath = location.state?.from === "achievement-directory" ? "/achievements" : profilePath
  const currentRecipient = recipientResult?.username === username ? recipientResult : null
  const recipient = currentRecipient?.profile

  useEffect(() => {
    let active = true
    const request = username ? getUserProfile(username) : getMyProfile()
    request.then(
      profile => { if (active) setRecipientResult({ username, profile, error: "" }) },
      error => { if (active) setRecipientResult({ username, profile: null, error: error instanceof Error ? error.message : "Не удалось загрузить пользователя" }) },
    )
    return () => { active = false }
  }, [username])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const cleanTitle = title.trim()
    const cleanDescription = description.trim()
    if (!recipient || !currentUser) return
    if (!cleanTitle || !cleanDescription || !image) {
      setFormError("Заполните название, описание и выберите изображение.")
      return
    }
    if (cleanTitle.length > 200 || cleanDescription.length > 5000) {
      setFormError("Название должно быть не длиннее 200, а описание — 5000 символов.")
      return
    }
    setSubmitting(true)
    setFormError("")
    setSuccess(false)
    try {
      await createAchievement(recipient.id, cleanTitle, cleanDescription, image)
      setTitle("")
      setDescription("")
      setImage(null)
      event.currentTarget.reset()
      setFormOpen(false)
      setSuccess(true)
      setRefreshAttempt(value => value + 1)
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Не удалось выдать ачивку")
    } finally {
      setSubmitting(false)
    }
  }

  return <Layout>
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 16 }}>
      <button type="button" onClick={() => navigate(backPath)}>← Назад</button>
    </div>
    <h1>Достижения</h1>
    {currentRecipient?.error && <p role="alert">{currentRecipient.error}</p>}
    {recipient && <section style={{ marginBottom: 24 }}>
      <button type="button" onClick={() => { setFormOpen(value => !value); setFormError(""); setSuccess(false) }}>
        Выдать ачивку
      </button>
      {formOpen && <form onSubmit={submit} style={{ display: "grid", gap: 10, maxWidth: 600, marginTop: 16 }}>
        <h2 id="issue-achievement-title" style={{ margin: 0 }}>Выдать ачивку пользователю {recipient.username}</h2>
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
      {success && <p role="status">Ачивка выдана.</p>}
    </section>}
    <ProfileAchievements key={`${username ?? "me"}:${refreshAttempt}`} username={username} />
  </Layout>
}
