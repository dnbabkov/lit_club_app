import { createContext } from "react"
import type { UserRead } from "../api/auth"

export type AuthStatus = "loading" | "authenticated" | "outside" | "denied" | "expired" | "error"
export type AuthContextValue = {
  user: UserRead | null
  isAuthenticated: boolean
  status: AuthStatus
  retry: () => void
  updateUser: (user: UserRead) => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
