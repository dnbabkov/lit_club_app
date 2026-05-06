import { useCallback, useEffect, useState, type SyntheticEvent } from "react"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { changeMyPassword, getMyProfile } from "../api/profile"
import { ProfileBookCard } from "../components/profile/ProfileBookCard"
import type { UserProfileRead } from "../types/profile"

function getRoleLabel(role: UserProfileRead["role"]): string {
  if (role === "admin") {
    return "Администратор"
  }

  if (role === "moderator") {
    return "Модератор"
  }

  return "Участник"
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return "Unexpected error"
}

export function ProfilePage() {
  const [profile, setProfile] = useState<UserProfileRead | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")

  const [isPasswordFormOpen, setIsPasswordFormOpen] = useState(false)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [newPasswordRepeat, setNewPasswordRepeat] = useState("")
  const [passwordErrorMessage, setPasswordErrorMessage] = useState("")
  const [passwordSuccessMessage, setPasswordSuccessMessage] = useState("")
  const [isPasswordSubmitting, setIsPasswordSubmitting] = useState(false)

  const loadProfileData = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")

    try {
      const data = await getMyProfile()
      setProfile(data)
    } catch (error) {
      setErrorMessage(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProfileData()
  }, [loadProfileData])

  async function handleChangePassword(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()

    setPasswordErrorMessage("")
    setPasswordSuccessMessage("")

    const trimmedCurrentPassword = currentPassword.trim()
    const trimmedNewPassword = newPassword.trim()
    const trimmedNewPasswordRepeat = newPasswordRepeat.trim()

    if (
      !trimmedCurrentPassword ||
      !trimmedNewPassword ||
      !trimmedNewPasswordRepeat
    ) {
      setPasswordErrorMessage("Заполните все поля.")
      return
    }

    if (trimmedNewPassword.length < 4 || trimmedNewPassword.length > 50) {
      setPasswordErrorMessage("Новый пароль должен быть от 4 до 50 символов.")
      return
    }

    if (trimmedNewPassword !== trimmedNewPasswordRepeat) {
      setPasswordErrorMessage("Новый пароль и повтор пароля не совпадают.")
      return
    }

    setIsPasswordSubmitting(true)

    try {
      await changeMyPassword({
        current_password: trimmedCurrentPassword,
        new_password: trimmedNewPassword,
      })

      setCurrentPassword("")
      setNewPassword("")
      setNewPasswordRepeat("")
      setPasswordSuccessMessage("Пароль успешно изменён.")
      setIsPasswordFormOpen(false)
    } catch (error) {
      setPasswordErrorMessage(getErrorMessage(error))
    } finally {
      setIsPasswordSubmitting(false)
    }
  }

  return (
    <Layout>
      <h1>Профиль</h1>

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && profile && (
        <>
          <div
            style={{
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: 16,
              marginBottom: 24,
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 12 }}>
              {profile.username}
            </h2>

            <p style={{ margin: "4px 0" }}>
              <strong>Telegram login:</strong> {profile.telegram_login}
            </p>

            <p style={{ margin: "4px 0" }}>
              <strong>Роль:</strong> {getRoleLabel(profile.role)}
            </p>

            <div style={{ marginTop: 16 }}>
              <button
                type="button"
                onClick={() => {
                  setIsPasswordFormOpen((value) => !value)
                  setPasswordErrorMessage("")
                  setPasswordSuccessMessage("")
                }}
              >
                {isPasswordFormOpen ? "Отменить" : "Изменить пароль"}
              </button>
            </div>

            {passwordSuccessMessage && (
              <p style={{ color: "green", marginTop: 12 }}>
                {passwordSuccessMessage}
              </p>
            )}

            {isPasswordFormOpen && (
              <form
                onSubmit={handleChangePassword}
                style={{
                  marginTop: 16,
                  display: "flex",
                  flexDirection: "column",
                  gap: 12,
                  maxWidth: 360,
                }}
              >
                <label>
                  Текущий пароль
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(event) => setCurrentPassword(event.target.value)}
                    minLength={4}
                    maxLength={50}
                    required
                    style={{
                      display: "block",
                      width: "100%",
                      marginTop: 4,
                    }}
                  />
                </label>

                <label>
                  Новый пароль
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(event) => setNewPassword(event.target.value)}
                    minLength={4}
                    maxLength={50}
                    required
                    style={{
                      display: "block",
                      width: "100%",
                      marginTop: 4,
                    }}
                  />
                </label>

                <label>
                  Повторите новый пароль
                  <input
                    type="password"
                    value={newPasswordRepeat}
                    onChange={(event) =>
                      setNewPasswordRepeat(event.target.value)
                    }
                    minLength={4}
                    maxLength={50}
                    required
                    style={{
                      display: "block",
                      width: "100%",
                      marginTop: 4,
                    }}
                  />
                </label>

                {passwordErrorMessage && (
                  <p style={{ color: "crimson", margin: 0 }}>
                    {passwordErrorMessage}
                  </p>
                )}

                <button type="submit" disabled={isPasswordSubmitting}>
                  {isPasswordSubmitting ? "Сохранение..." : "Сохранить пароль"}
                </button>
              </form>
            )}
          </div>

          <div>
            <h2>Предложенные книги</h2>

            {profile.nominated_books.length === 0 ? (
              <p>Вы пока не предлагали ни одной книги.</p>
            ) : (
              profile.nominated_books.map((item) => (
                <ProfileBookCard key={item.book_id} item={item} />
              ))
            )}
          </div>
        </>
      )}
    </Layout>
  )
}