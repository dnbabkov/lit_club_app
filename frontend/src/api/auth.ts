import { post } from "./http"

export type RegisterPayload = {
    username: string
    telegram_login: string
    password: string
}

export type LoginPayload = {
    telegram_login: string
    password: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
}

export async function registerUser(
    payload: RegisterPayload
): Promise<TokenResponse> {
    return post<TokenResponse>("/users/register", payload)
}

export async function loginUser(
    payload: LoginPayload
): Promise<TokenResponse> {
    return post<TokenResponse>("/users/login", payload)
}