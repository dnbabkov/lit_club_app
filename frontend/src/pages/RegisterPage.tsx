import { useState, type SyntheticEvent } from "react";
import {Link, Navigate, useNavigate} from "react-router-dom";
import { ApiError } from "../api/http.ts";
import { useAuth } from "../auth/AuthContext.tsx";

export function RegisterPage() {
    const navigate = useNavigate()
    const { register, isAuthenticated } = useAuth()

    const [username, setUsername] = useState("")
    const [telegramLogin, setTelegramLogin] = useState("")
    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [errorMessage, setErrorMessage] = useState("")
    const [isSubmitting, setIsSubmitting] = useState(false)

    if (isAuthenticated) {
        return <Navigate to="/" replace />
    }

    async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
        event.preventDefault()
        setErrorMessage("")

        if (password !== confirmPassword) {
            setErrorMessage("Пароли не совпадают")
            return
        }

        setIsSubmitting(true)

        try {
            await register({
                username,
                telegram_login: telegramLogin,
                password
            })

            navigate("/")
        } catch (error) {
            if (error instanceof ApiError) {
                setErrorMessage(error.message)
            } else {
                setErrorMessage("Unknown error")
            }
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <div style={{ maxWidth: 400, margin: "40px auto" }}>
          <h1>Регистрация</h1>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 12 }}>
              <label htmlFor="username">Имя пользователя</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
              />
            </div>

            <div style={{ marginBottom: 12 }}>
              <label htmlFor="telegram_login">Telegram login</label>
              <input
                id="telegram_login"
                type="text"
                value={telegramLogin}
                onChange={(event) => setTelegramLogin(event.target.value)}
                placeholder="@your_login или your_login"
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

            <div style={{ marginBottom: 12 }}>
              <label htmlFor="confirm_password">Подтверждение пароля</label>
              <input
                id="confirm_password"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
              />
            </div>

            {errorMessage && (
              <div style={{ color: "crimson", marginBottom: 12 }}>
                {errorMessage}
              </div>
            )}

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Регистрируем..." : "Зарегистрироваться"}
            </button>
          </form>

          <p style={{ marginTop: 16 }}>
            <Link to="/login">Войти</Link>
          </p>
        </div>
    )
}