import { useEffect, useState } from "react"
import { Link, useLocation } from "react-router-dom"
import { useAuth } from "../auth/useAuth"

export function NavBar() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  const [menuPath, setMenuPath] = useState<string | null>(null)
  const isMobileMenuOpen = menuPath === location.pathname

  useEffect(() => {
    if (!isMobileMenuOpen) {
      return
    }

    const previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuPath(null)
      }
    }

    window.addEventListener("keydown", handleKeyDown)

    return () => {
      document.body.style.overflow = previousBodyOverflow
      window.removeEventListener("keydown", handleKeyDown)
    }
  }, [isMobileMenuOpen])

  function closeMobileMenu() {
    setMenuPath(null)
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
        onClick={() => setMenuPath(isMobileMenuOpen ? null : location.pathname)}
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
        onClick={closeMobileMenu}
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
            <Link to="/comics" className="navbar__link">
              Комикс
            </Link>

            <Link to="/users" className="navbar__link">
              Пользователи
            </Link>

            <Link to="/profile" className="navbar__link">
              Профиль
            </Link>
          </>
        ) : null}
      </nav>
    </header>
  )
}
