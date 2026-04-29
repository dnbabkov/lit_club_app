import { createContext, useContext, useMemo, useState, type ReactNode } from "react"
import { loginUser, registerUser, type LoginPayload, type RegisterPayload } from "../api/auth.ts";
import { getToken, setToken, removeToken } from "./token.ts";

type AuthContextValue = {
    token: string | null
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

    async function login(payload: LoginPayload): Promise<void> {
        const data = await loginUser(payload)
        setToken(data.access_token)
        setTokenState(data.access_token)
    }

    async function register(payload: RegisterPayload) : Promise<void> {
        const data = await registerUser(payload)
        setToken(data.access_token)
        setTokenState(data.access_token)
    }

    function logout(): void {
        removeToken()
        setTokenState(null)
    }

    const value = useMemo<AuthContextValue>(
        () => ({
            token,
            isAuthenticated: token !== null,
            login,
            register,
            logout,
        }),
        [token]
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