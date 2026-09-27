import type { ReactNode } from "react"
import { useAuth } from "../auth/useAuth"

type ProtectedRouteProps = {
  children: ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, status, retry } = useAuth()

  if (!isAuthenticated) {
    const messages = {
      loading: "Проверяем доступ…",
      outside: "Откройте приложение через кнопку в Telegram-боте.",
      denied: "Доступ не выдан. Обратитесь к администратору клуба.",
      expired: "Данные Telegram недействительны или устарели. Закройте Mini App и откройте его заново через бота.",
      error: "Не удалось выполнить вход. Проверьте соединение и попробуйте снова.",
      authenticated: "",
    }
    return (
      <main style={{ maxWidth: 480, margin: "48px auto", padding: 24 }}>
        <h1>Литературный клуб</h1>
        <p role="status" aria-live="polite">{messages[status]}</p>
        {(status === "denied" || status === "error") && (
          <button type="button" onClick={retry}>
            {status === "denied" ? "Проверить доступ" : "Повторить вход"}
          </button>
        )}
      </main>
    )
  }

  return <>{children}</>
}
