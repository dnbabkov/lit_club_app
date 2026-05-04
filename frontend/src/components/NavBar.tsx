import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { getCurrentUser } from "../api/auth"
import { useAuth } from "../auth/AuthContext.tsx"
import type { UserRead } from "../api/auth"

export function NavBar() {
  const { isAuthenticated, logout } = useAuth()
  const [currentUser, setCurrentUser] = useState<UserRead | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      setCurrentUser(null)
      return
    }

    let ignore = false

    async function loadCurrentUser() {
      try {
        const user = await getCurrentUser()

        if (!ignore) {
          setCurrentUser(user)
        }
      } catch {
        if (!ignore) {
          setCurrentUser(null)
        }
      }
    }

    loadCurrentUser()

    return () => {
      ignore = true
    }
  }, [isAuthenticated])

  const isAdmin = currentUser?.role === "admin"

  return (
    <header
      style={{
        borderBottom: "1px solid #ddd",
        padding: "16px 24px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <div>
        <Link
          to="/"
          style={{ fontWeight: "bold", textDecoration: "none", color: "black" }}
        >
          Литературный клуб
        </Link>
      </div>

      <nav style={{ display: "flex", gap: 16, alignItems: "center" }}>
        {isAuthenticated ? (
          <>
            <Link to="/meetings">Встречи</Link>
            <Link to="/selection">Выбор книги</Link>
            <Link to="/books/finished">Прочитанные книги</Link>
            <Link to="/books">Все книги</Link>

            {isAdmin && <Link to="/users">Пользователи</Link>}

            <Link to="/profile">Профиль</Link>
            <button type="button" onClick={logout}>
              Выйти
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Войти</Link>
            <Link to="/register">Регистрация</Link>
          </>
        )}
      </nav>
    </header>
  )
}