import { useState, type SyntheticEvent } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { ApiError } from "../api/http.ts"
import { useAuth } from "../auth/AuthContext.tsx"

export function LoginPage() {
  const navigate = useNavigate()
  const { login, isAuthenticated } = useAuth()

  const [telegramLogin, setTelegramLogin] = useState("")
  const [password, setPassword] = useState("")
  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")
    setIsSubmitting(true)

    try {
      await login({
        telegram_login: telegramLogin,
        password: password,
      })

      navigate("/")
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "40px auto" }}>
      <h1>Вход</h1>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <label htmlFor="telegram_login">Telegram login</label>
          <input
            id="telegram_login"
            type="text"
            value={telegramLogin}
            onChange={(event) => setTelegramLogin(event.target.value)}
            placeholder="@telegram_login или telegram_login"
            style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label htmlFor="password">Пароль</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
          />
        </div>

        {errorMessage && (
          <div style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</div>
        )}

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Входим..." : "Войти"}
        </button>
      </form>

      <button
        type="button"
        onClick={() => setIsForgotPasswordOpen(true)}
        style={{
          display: "inline-block",
          marginTop: 12,
          padding: 0,
          border: 0,
          background: "transparent",
          color: "var(--accent)",
          cursor: "pointer",
          font: "inherit",
          textDecoration: "underline",
        }}
      >
        Забыли пароль?
      </button>

      <p style={{ marginTop: 16 }}>
        <Link to="/register">Регистрация</Link>
      </p>

      {isForgotPasswordOpen && (
        <div
          role="presentation"
          onClick={() => setIsForgotPasswordOpen(false)}
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
            aria-labelledby="forgot-password-title"
            onClick={(event) => event.stopPropagation()}
            style={{
              width: "min(360px, 100%)",
              padding: 20,
              borderRadius: 12,
              border: "1px solid var(--border)",
              background: "var(--bg)",
              boxShadow: "var(--shadow)",
              textAlign: "left",
            }}
          >
            <h2 id="forgot-password-title" style={{ marginBottom: 12 }}>
              Забыли пароль?
            </h2>
            <p style={{ marginBottom: 8 }}>
              Для сброса пароля обратитесь к админу (создателю сайта).
            </p>
            <p style={{ marginBottom: 16, fontSize: 14 }}>
              *временная мера до введения интеграции с ТГ
            </p>
            <div style={{ textAlign: "right" }}>
              <button type="button" onClick={() => setIsForgotPasswordOpen(false)}>
                ОК
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}