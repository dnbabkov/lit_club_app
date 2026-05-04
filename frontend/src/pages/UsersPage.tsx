import { useCallback, useEffect, useState } from "react"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { getCurrentUser, getUsers } from "../api/auth"
import type { UserRead } from "../api/auth"

function formatTelegramLogin(telegramLogin: string): string {
  return telegramLogin.startsWith("@") ? telegramLogin : `@${telegramLogin}`
}

export function UsersPage() {
  const [users, setUsers] = useState<UserRead[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")
  const [isForbidden, setIsForbidden] = useState(false)

  const loadUsers = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")
    setIsForbidden(false)

    try {
      const currentUser = await getCurrentUser()

      if (currentUser.role !== "admin") {
        setUsers([])
        setIsForbidden(true)
        return
      }

      const usersData = await getUsers()
      setUsers(usersData)
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUsers()
  }, [loadUsers])

  return (
    <Layout>
      <h1>Пользователи</h1>

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && isForbidden && (
        <p style={{ color: "crimson" }}>
          У вас нет прав для просмотра этой страницы.
        </p>
      )}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !isForbidden && !errorMessage && users.length === 0 && (
        <p>Пользователи не найдены.</p>
      )}

      {!isLoading && !isForbidden && !errorMessage && users.length > 0 && (
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
            </tr>
          </thead>

          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td style={{ borderBottom: "1px solid #eee", padding: 8 }}>
                  {user.username}
                </td>
                <td style={{ borderBottom: "1px solid #eee", padding: 8 }}>
                  {formatTelegramLogin(user.telegram_login)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Layout>
  )
}