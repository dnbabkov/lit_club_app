import { useCallback, useEffect, useState, type SyntheticEvent } from "react"
import { useNavigate } from "react-router-dom"
import {
  changeUserPassword,
  getCurrentUser,
  getPublicUsers,
  getUsers,
  type UserPublicRead,
  type UserRead,
} from "../api/auth"
import { ApiError } from "../api/http"
import { Layout } from "../components/Layout"

type UsersPageUser = UserRead | UserPublicRead

function formatTelegramLogin(telegramLogin: string): string {
  return telegramLogin.startsWith("@") ? telegramLogin : `@${telegramLogin}`
}

function getRoleLabel(role: UserRead["role"]): string {
  if (role === "admin") {
    return "Админ"
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

function hasFullUserData(user: UsersPageUser): user is UserRead {
  return "telegram_login" in user && "role" in user
}

function UserAvatarPlaceholder({ username }: { username: string }) {
  const initial = username.trim().charAt(0).toUpperCase() || "?"

  return (
    <div
      aria-hidden="true"
      style={{
        width: 40,
        height: 40,
        borderRadius: "50%",
        border: "1px solid #ddd",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: 600,
        flexShrink: 0,
      }}
    >
      {initial}
    </div>
  )
}

export function UsersPage() {
  const navigate = useNavigate()

  const [currentUser, setCurrentUser] = useState<UserRead | null>(null)
  const [users, setUsers] = useState<UsersPageUser[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")
  const [successMessage, setSuccessMessage] = useState("")

  const [selectedUser, setSelectedUser] = useState<UserRead | null>(null)
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [passwordErrorMessage, setPasswordErrorMessage] = useState("")
  const [isPasswordSubmitting, setIsPasswordSubmitting] = useState(false)

  const isAdmin = currentUser?.role === "admin"

  const adminUsers = users.filter(
    (user): user is UserRead => hasFullUserData(user) && user.role !== "admin"
  )

  const publicUsers = users.filter((user) => {
    if (!hasFullUserData(user)) {
      return true
    }

    return user.role !== "admin"
  })

  const visibleUsers = isAdmin ? adminUsers : publicUsers

  const loadUsers = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")
    setSuccessMessage("")

    try {
      const currentUserData = await getCurrentUser()
      setCurrentUser(currentUserData)

      if (currentUserData.role === "admin") {
        const usersData = await getUsers()
        setUsers(usersData.filter((user) => user.role !== "admin"))
      } else {
        const usersData = await getPublicUsers()
        setUsers(usersData)
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUsers()
  }, [loadUsers])

  function openUserProfile(username: string) {
    navigate(`/users/${encodeURIComponent(username)}/profile`)
  }

  function openPasswordModal(user: UserRead) {
    setSelectedUser(user)
    setNewPassword("")
    setConfirmPassword("")
    setPasswordErrorMessage("")
    setSuccessMessage("")
  }

  function closePasswordModal() {
    if (isPasswordSubmitting) {
      return
    }

    setSelectedUser(null)
    setNewPassword("")
    setConfirmPassword("")
    setPasswordErrorMessage("")
  }

  async function handlePasswordSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!selectedUser) {
      return
    }

    setPasswordErrorMessage("")
    setSuccessMessage("")

    if (newPassword.length < 4) {
      setPasswordErrorMessage("Пароль должен содержать минимум 4 символа.")
      return
    }

    if (newPassword.length > 50) {
      setPasswordErrorMessage("Пароль должен содержать не больше 50 символов.")
      return
    }

    if (newPassword !== confirmPassword) {
      setPasswordErrorMessage("Пароли не совпадают.")
      return
    }

    setIsPasswordSubmitting(true)

    try {
      await changeUserPassword(selectedUser.id, {
        new_password: newPassword,
      })

      setSuccessMessage(`Пароль пользователя ${selectedUser.username} изменён.`)
      setSelectedUser(null)
      setNewPassword("")
      setConfirmPassword("")
      setPasswordErrorMessage("")
    } catch (error) {
      setPasswordErrorMessage(getErrorMessage(error))
    } finally {
      setIsPasswordSubmitting(false)
    }
  }

  return (
    <Layout>
      <h1>Пользователи</h1>

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && successMessage && (
        <p style={{ color: "green", marginBottom: 12 }}>{successMessage}</p>
      )}

      {!isLoading && !errorMessage && visibleUsers.length === 0 && (
        <p>Пользователи не найдены.</p>
      )}

      {!isLoading && !errorMessage && !isAdmin && visibleUsers.length > 0 && (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 12,
            marginTop: 16,
          }}
        >
          {visibleUsers.map((user) => (
            <div
              key={user.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                border: "1px solid #ddd",
                borderRadius: 8,
                padding: 12,
                textAlign: "left",
              }}
            >
              <UserAvatarPlaceholder username={user.username} />

              <strong
                style={{
                  flex: 1,
                  minWidth: 0,
                  overflowWrap: "anywhere",
                }}
              >
                {user.username}
              </strong>

              <span aria-hidden="true">—</span>

              <button
                type="button"
                onClick={() => openUserProfile(user.username)}
              >
                Перейти в профиль
              </button>
            </div>
          ))}
        </div>
      )}

      {!isLoading && !errorMessage && isAdmin && adminUsers.length > 0 && (
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            marginTop: 16,
          }}
        >
          <thead>
            <tr>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #ddd",
                  padding: 8,
                }}
              >
                Юзернейм
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #ddd",
                  padding: 8,
                }}
              >
                Тег
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #ddd",
                  padding: 8,
                }}
              >
                Роль
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #ddd",
                  padding: 8,
                }}
              >
                Действия
              </th>
            </tr>
          </thead>

          <tbody>
            {adminUsers.map((user) => (
              <tr key={user.id}>
                <td style={{ borderBottom: "1px solid #eee", padding: 8 }}>
                  {user.username}
                </td>
                <td style={{ borderBottom: "1px solid #eee", padding: 8 }}>
                  {formatTelegramLogin(user.telegram_login)}
                </td>
                <td style={{ borderBottom: "1px solid #eee", padding: 8 }}>
                  {getRoleLabel(user.role)}
                </td>
                <td style={{ borderBottom: "1px solid #eee", padding: 8 }}>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button
                      type="button"
                      onClick={() => openUserProfile(user.username)}
                    >
                      Перейти в профиль
                    </button>

                    <button
                      type="button"
                      onClick={() => openPasswordModal(user)}
                    >
                      Изменить пароль пользователя
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {selectedUser && (
        <div
          role="presentation"
          onClick={closePasswordModal}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 16,
            background: "rgba(0, 0, 0, 0.45)",
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="change-user-password-title"
            onClick={(event) => event.stopPropagation()}
            style={{
              width: "min(420px, 100%)",
              padding: 24,
              borderRadius: 12,
              border: "1px solid var(--border)",
              background: "var(--bg)",
              boxShadow: "var(--shadow)",
              textAlign: "left",
            }}
          >
            <h2 id="change-user-password-title">
              Изменить пароль пользователя
            </h2>

            <p style={{ marginBottom: 16 }}>
              Пользователь: <strong>{selectedUser.username}</strong>{" "}
              ({formatTelegramLogin(selectedUser.telegram_login)})
            </p>

            <form onSubmit={handlePasswordSubmit}>
              <div style={{ marginBottom: 12 }}>
                <label htmlFor="new_user_password">Новый пароль</label>
                <input
                  id="new_user_password"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  minLength={4}
                  maxLength={50}
                  required
                  style={{
                    display: "block",
                    width: "100%",
                    padding: 8,
                    marginTop: 4,
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ marginBottom: 12 }}>
                <label htmlFor="confirm_new_user_password">
                  Повторите пароль
                </label>
                <input
                  id="confirm_new_user_password"
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  minLength={4}
                  maxLength={50}
                  required
                  style={{
                    display: "block",
                    width: "100%",
                    padding: 8,
                    marginTop: 4,
                    boxSizing: "border-box",
                  }}
                />
              </div>

              {passwordErrorMessage && (
                <div style={{ color: "crimson", marginBottom: 12 }}>
                  {passwordErrorMessage}
                </div>
              )}

              <div
                style={{
                  display: "flex",
                  gap: 8,
                  justifyContent: "flex-end",
                }}
              >
                <button
                  type="button"
                  onClick={closePasswordModal}
                  disabled={isPasswordSubmitting}
                >
                  Отмена
                </button>

                <button type="submit" disabled={isPasswordSubmitting}>
                  {isPasswordSubmitting ? "Сохраняем..." : "Сохранить"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  )
}