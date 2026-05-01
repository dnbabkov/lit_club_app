import { useState, type SyntheticEvent } from "react";
import { Link, useNavigate, Navigate} from "react-router-dom";
import { ApiError } from "../api/http.ts";
import { useAuth } from "../auth/AuthContext.tsx";

export function LoginPage() {
  const navigate = useNavigate()
  const {login, isAuthenticated} = useAuth()

  const [telegramLogin, setTelegramLogin] = useState("")
  const [password, setPassword] = useState("")
  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>){
    event.preventDefault()
    setErrorMessage("")
    setIsSubmitting(true)

    try {
      await login({
        telegram_login: telegramLogin,
        password: password
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
        <div style={{maxWidth: 400, margin: "40px auto"}}>
          <h1>Вход</h1>

          <form onSubmit={handleSubmit}>
            <div style={{marginBottom: 12}}>
              <label htmlFor="telegram_login">Telegram login</label>
              <input
                  id="telegram_login"
                  type="text"
                  value={telegramLogin}
                  onChange={(event) => setTelegramLogin(event.target.value)}
                  placeholder="@telegram_login или telegram_login"
                  style={{display: "block", width: "100%", padding: 8, marginTop: 4}}
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
              <div style={{ color: "crimson", marginBottom: 12 }}>
                {errorMessage}
              </div>
            )}

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Входим..." : "Войти"}
            </button>

          </form>

          <p style={{ marginTop: 16 }}>
            <Link to="/register">Регистрация</Link>
          </p>

        </div>
    )
}