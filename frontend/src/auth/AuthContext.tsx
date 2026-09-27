import { useEffect, useState, type ReactNode } from "react"
import { getCurrentUser, loginTelegram } from "../api/auth"
import { ApiError } from "../api/http"
import { AuthContext, type AuthContextValue, type AuthStatus } from "./context"
import { clearLegacyToken, onSessionFailure, removeToken, setToken } from "./token"
import { getTelegramApp } from "./telegram"

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<Pick<AuthContextValue, "user" | "status">>({
    user: null, status: "loading",
  })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    let signingIn = false
    const telegram = getTelegramApp()
    clearLegacyToken()
    removeToken()
    telegram?.ready()
    telegram?.expand()

    async function signIn() {
      if (signingIn || !active) return
      signingIn = true
      setState({ user: null, status: "loading" })
      removeToken()
      try {
        if (!telegram?.initData) {
          setState({ user: null, status: "outside" })
          return
        }
        const session = await loginTelegram(telegram.initData)
        if (!active) return
        // Do not publish the token until the account check has also succeeded.
        const user = await getCurrentUser(session.access_token)
        if (!active) return
        setToken(session.access_token)
        setState({ user, status: "authenticated" })
      } catch (error) {
        if (!active) return
        const status: AuthStatus = error instanceof ApiError && error.status === 403
          ? "denied"
          : error instanceof ApiError && error.status === 401 ? "expired" : "error"
        removeToken()
        setState({ user: null, status })
      } finally {
        signingIn = false
      }
    }

    const unsubscribe = onSessionFailure(status => {
      if (status === 403) setState({ user: null, status: "denied" })
      else void signIn()
    })
    // Scheduling also prevents the discarded StrictMode effect from sending a login.
    void Promise.resolve().then(signIn)
    return () => {
      active = false
      unsubscribe()
      removeToken()
    }
  }, [attempt])

  function retry() {
    setState({ user: null, status: "loading" })
    setAttempt(value => value + 1)
  }

  return (
    <AuthContext.Provider value={{ ...state, isAuthenticated: state.status === "authenticated", retry }}>
      {children}
    </AuthContext.Provider>
  )
}
