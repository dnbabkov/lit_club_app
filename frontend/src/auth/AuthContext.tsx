import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import {
  loginUser,
  registerUser,
  getCurrentUser,
  type LoginPayload,
  type RegisterPayload,
  type UserRead,
} from "../api/auth"
import { getToken, setToken, removeToken } from "./token"

type AuthContextValue = {
  token: string | null
  user: UserRead | null
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

type AuthProviderProps = {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setTokenState] = useState<string | null>(() => getToken())
  const [user, setUser] = useState<UserRead | null>(null)

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setUser(null)
        return
      }

      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
      } catch {
        removeToken()
        setTokenState(null)
        setUser(null)
      }
    }

    loadUser()
  }, [token])

  async function login(payload: LoginPayload): Promise<void> {
    const data = await loginUser(payload)
    setToken(data.access_token)
    setTokenState(data.access_token)

    const currentUser = await getCurrentUser()
    setUser(currentUser)
  }

  async function register(payload: RegisterPayload): Promise<void> {
    const data = await registerUser(payload)
    setToken(data.access_token)
    setTokenState(data.access_token)

    const currentUser = await getCurrentUser()
    setUser(currentUser)
  }

  function logout(): void {
    removeToken()
    setTokenState(null)
    setUser(null)
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAuthenticated: token !== null,
      login,
      register,
      logout,
    }),
    [token, user]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider")
  }

  return context
}