import { get, post } from "./http"

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

export type UserRead = {
  id: number
  username: string
  telegram_login: string
  role: "member" | "moderator"
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

export async function getCurrentUser(): Promise<UserRead> {
  return get<UserRead>("/users/me")
}