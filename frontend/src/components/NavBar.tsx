import { useEffect, useState } from "react"
import { Link, useLocation } from "react-router-dom"
import { getCurrentUser } from "../api/auth"
import { useAuth } from "../auth/AuthContext.tsx"
import type { UserRead } from "../api/auth"

export function NavBar() {
  const { isAuthenticated, logout } = useAuth()
  const location = useLocation()
  const [currentUser, setCurrentUser] = useState<UserRead | null>(null)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

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

  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!isMobileMenuOpen) {
      return
    }

    const previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsMobileMenuOpen(false)
      }
    }

    window.addEventListener("keydown", handleKeyDown)

    return () => {
      document.body.style.overflow = previousBodyOverflow
      window.removeEventListener("keydown", handleKeyDown)
    }
  }, [isMobileMenuOpen])

  const isAdmin = currentUser?.role === "admin"

  function closeMobileMenu() {
    setIsMobileMenuOpen(false)
  }

  function handleLogout() {
    closeMobileMenu()
    logout()
  }

  return (
    <header className="navbar">
      <Link to="/" className="navbar__brand" onClick={closeMobileMenu}>
        Литературный клуб
      </Link>

      <button
        type="button"
        className="navbar__burger"
        aria-label={isMobileMenuOpen ? "Закрыть меню" : "Открыть меню"}
        aria-expanded={isMobileMenuOpen}
        aria-controls="site-navigation"
        onClick={() => setIsMobileMenuOpen((isOpen) => !isOpen)}
      >
        <span />
        <span />
        <span />
      </button>

      <button
        type="button"
        className={`navbar__overlay${isMobileMenuOpen ? " navbar__overlay--open" : ""}`}
        aria-label="Закрыть меню"
        onClick={closeMobileMenu}
      />

      <nav
        id="site-navigation"
        className={`navbar__links${isMobileMenuOpen ? " navbar__links--open" : ""}`}
      >
        <div className="navbar__mobile-header">
          <span>Меню</span>
          <button
            type="button"
            className="navbar__close"
            aria-label="Закрыть меню"
            onClick={closeMobileMenu}
          >
            ×
          </button>
        </div>

        {isAuthenticated ? (
          <>
            <Link to="/meetings" className="navbar__link">
              Встречи
            </Link>
            <Link to="/selection" className="navbar__link">
              Выбор книги
            </Link>
            <Link to="/books/finished" className="navbar__link">
              Прочитанные книги
            </Link>
            <Link to="/books" className="navbar__link">
              Все книги
            </Link>

            {isAdmin && (
              <Link to="/users" className="navbar__link">
                Пользователи
              </Link>
            )}

            <Link to="/profile" className="navbar__link">
              Профиль
            </Link>
            <button type="button" className="navbar__link-button" onClick={handleLogout}>
              Выйти
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="navbar__link">
              Войти
            </Link>
            <Link to="/register" className="navbar__link">
              Регистрация
            </Link>
          </>
        )}
      </nav>
    </header>
  )
}