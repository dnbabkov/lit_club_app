import { useState, type SyntheticEvent } from "react"
import { createUser, updateUser, type UserAdminRead } from "../api/auth"
import { ApiError } from "../api/http"

export function UserEditor({ user, onSaved, onClose }: {
  user: UserAdminRead | null
  onSaved: (user: UserAdminRead) => void
  onClose: () => void
}) {
  const [name, setName] = useState(user?.username ?? "")
  const [telegramId, setTelegramId] = useState(user?.tg_id ?? "")
  const [login, setLogin] = useState(user?.telegram_login ?? "")
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)

  async function submit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    const id = telegramId.trim()
    if (!name.trim()) { setError("Введите имя пользователя"); return }
    if (id && (!/^[0-9]+$/.test(id) || BigInt(id) < 1n || BigInt(id) > 9223372036854775807n)) {
      setError("Введите положительный числовой Telegram ID в пределах BIGINT")
      return
    }
    setSaving(true)
    setError("")
    try {
      const payload = { username: name.trim(), tg_id: id || null, telegram_login: login.trim() || null }
      const result = user ? await updateUser(user.id, payload) : await createUser(payload)
      onSaved(result)
    } catch (error) {
      setError(error instanceof ApiError && error.status === 422
        ? "Проверьте поля: Telegram-ник может содержать только латинские буквы, цифры и подчёркивания."
        : error instanceof Error ? error.message : "Не удалось сохранить пользователя")
    } finally {
      setSaving(false)
    }
  }

  return (
    <section role="dialog" aria-labelledby="user-editor-title" style={{ border: "1px solid var(--border)", borderRadius: 12, padding: 20, margin: "16px 0", textAlign: "left" }}>
      <h2 id="user-editor-title">{user ? "Редактировать пользователя" : "Новый пользователь"}</h2>
      <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
        <label>Имя<input autoFocus required maxLength={50} value={name} onChange={event => setName(event.target.value)} disabled={saving} style={{ display: "block", width: "100%", boxSizing: "border-box" }} /></label>
        <label>Telegram ID<input inputMode="numeric" maxLength={19} value={telegramId} onChange={event => setTelegramId(event.target.value)} disabled={saving} style={{ display: "block", width: "100%", boxSizing: "border-box" }} /></label>
        <small>Без Telegram ID аккаунт сохранится, но войти через Telegram пока не сможет.</small>
        <label>Telegram-ник<input placeholder="@username" maxLength={65} value={login} onChange={event => setLogin(event.target.value)} disabled={saving} style={{ display: "block", width: "100%", boxSizing: "border-box" }} /></label>
        {error && <p role="alert" style={{ color: "crimson" }}>{error}</p>}
        <div style={{ display: "flex", gap: 8 }}>
          <button type="submit" disabled={saving}>{saving ? "Сохраняем…" : "Сохранить"}</button>
          <button type="button" disabled={saving} onClick={onClose}>Отмена</button>
        </div>
      </form>
    </section>
  )
}
