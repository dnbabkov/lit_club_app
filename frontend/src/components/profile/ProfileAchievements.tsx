import { useEffect, useRef, useState } from "react"
import { deleteAchievement, getAchievementImage, getMyAchievements, getUserAchievements, type AchievementRead } from "../../api/achievements"
import { useAuth } from "../../auth/useAuth"

function AchievementCard({ achievement, canDelete, onDeleted }: { achievement: AchievementRead, canDelete: boolean, onDeleted: () => void }) {
  const cardRef = useRef<HTMLElement>(null)
  const [url, setUrl] = useState<string | null>(null)
  const [error, setError] = useState("")
  const [deleteError, setDeleteError] = useState("")
  const [deleting, setDeleting] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let objectUrl: string | undefined
    let started = false
    const loadImage = () => {
      if (started) return
      started = true
      getAchievementImage(achievement.image_url, controller.signal).then(blob => {
        if (controller.signal.aborted) return
        objectUrl = URL.createObjectURL(blob)
        setUrl(objectUrl)
      }).catch(error => {
        if (!controller.signal.aborted) setError(error instanceof Error ? error.message : "Не удалось загрузить ачивку")
      })
    }
    const observer = typeof IntersectionObserver === "undefined"
      ? null
      : new IntersectionObserver(entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          loadImage()
          observer?.disconnect()
        }
      }, { rootMargin: "200px" })
    if (observer && cardRef.current) observer.observe(cardRef.current)
    else loadImage()
    return () => {
      controller.abort()
      observer?.disconnect()
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [achievement.image_url, attempt])

  return <article ref={cardRef} style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12, minWidth: 0, display: "grid", gridTemplateColumns: "minmax(0, 3fr) minmax(80px, 1fr)", gap: 12, alignItems: "center" }}>
    <div style={{ minWidth: 0 }}>
      {error ? <div role="alert">
        <p>{error}</p>
        <button type="button" onClick={() => { setError(""); setUrl(null); setAttempt(value => value + 1) }}>Повторить</button>
      </div> : url ? <img
        src={url}
        alt={`Ачивка №${achievement.id}`}
        style={{ display: "block", width: "100%", height: "auto", borderRadius: 8 }}
        onError={() => setError("Не удалось показать изображение ачивки")}
      /> : <p role="status">Загрузка ачивки…</p>}
    </div>
    <div style={{ minWidth: 0, textAlign: "center", overflowWrap: "anywhere" }}>
      <div aria-hidden="true" style={{ width: 48, height: 48, borderRadius: "50%", border: "1px solid #ddd", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 600, margin: "0 auto 8px" }}>
        {achievement.giver.username.trim().charAt(0).toUpperCase() || "?"}
      </div>
      <small style={{ display: "block", marginBottom: 4 }}>Выдал(а)</small>
      <strong>{achievement.giver.username}</strong>
      {canDelete && <button type="button" style={{ display: "block", margin: "12px auto 0" }} onClick={() => {
        setDeleteError("")
        setConfirmingDelete(true)
      }} disabled={deleting}>{deleting ? "Удаление…" : "Удалить ачивку"}</button>}
      {canDelete && confirmingDelete && <div role="alertdialog" aria-labelledby={`delete-achievement-title-${achievement.id}`} aria-describedby={`delete-achievement-description-${achievement.id}`} style={{ marginTop: 12 }}>
        <strong id={`delete-achievement-title-${achievement.id}`}>Удалить ачивку?</strong>
        <p id={`delete-achievement-description-${achievement.id}`}>Это действие нельзя отменить.</p>
        <div style={{ display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap" }}>
          <button type="button" onClick={() => {
            setConfirmingDelete(false)
            setDeleteError("")
          }} disabled={deleting}>Отмена</button>
          <button type="button" onClick={async () => {
            if (deleting) return
            setDeleting(true)
            setDeleteError("")
            try {
              await deleteAchievement(achievement.id)
              setConfirmingDelete(false)
              onDeleted()
            } catch (error) {
              setDeleteError(error instanceof Error ? error.message : "Не удалось удалить ачивку")
            } finally {
              setDeleting(false)
            }
          }} disabled={deleting}>{deleting ? "Удаление…" : "Подтвердить удаление"}</button>
        </div>
      </div>}
      {deleteError && <p role="alert">{deleteError}</p>}
    </div>
  </article>
}

export function ProfileAchievements({ username }: { username?: string }) {
  const { user: currentUser } = useAuth()
  const [achievements, setAchievements] = useState<AchievementRead[] | null>(null)
  const [error, setError] = useState("")
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const request = username ? getUserAchievements(username, controller.signal) : getMyAchievements(controller.signal)
    request.then(data => { if (!controller.signal.aborted) setAchievements(data) })
      .catch(error => {
        if (!controller.signal.aborted) setError(error instanceof Error ? error.message : "Не удалось загрузить ачивки")
      })
    return () => controller.abort()
  }, [username, attempt])

  const refresh = () => setAttempt(value => value + 1)

  return <section aria-labelledby="profile-achievements-title" style={{ marginBottom: 24 }}>
    <h2 id="profile-achievements-title">Достижения{achievements?.length ? ` (${achievements.length})` : ""}</h2>
    {username && <p>{username}</p>}
    {error ? <div role="alert"><p>{error}</p><button type="button" onClick={() => { setError(""); setAttempt(value => value + 1) }}>Повторить</button></div>
      : achievements === null ? <p role="status">Загрузка достижений…</p>
      : achievements.length === 0 ? <p>{username ? "У пользователя пока нет достижений." : "У вас пока нет достижений."}</p>
      : <div style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 960, margin: "0 auto" }}>
          {achievements.map(achievement => <AchievementCard key={`${username ?? "me"}:${achievement.id}`} achievement={achievement}
           canDelete={currentUser?.role === "admin" || currentUser?.id === achievement.giver.id}
           onDeleted={refresh} />)}
      </div>}
  </section>
}
