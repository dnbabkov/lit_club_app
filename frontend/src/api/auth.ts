import { get, request, post, patch } from "./http"

export type TokenResponse = {
  access_token: string
  token_type: string
}

export type UserRead = {
  id: number
  username: string
  telegram_login: string | null
  role: "member" | "moderator" | "admin"
}

export type UserPublicRead = {
  id: number
  username: string
}

export async function loginTelegram(initData: string): Promise<TokenResponse> {
  return request<TokenResponse>("/users/auth/telegram", {
    method: "POST", body: { init_data: initData }, token: null,
  })
}

export async function getCurrentUser(token?: string): Promise<UserRead> {
  return request<UserRead>("/users/me", { token })
}

export type UserAdminRead = UserRead & { tg_id: string | null }
export type UserAdminWrite = { username: string; tg_id: string | null; telegram_login: string | null }

export async function createUser(payload: UserAdminWrite): Promise<UserAdminRead> {
  return post<UserAdminRead>("/users/", payload)
}

export async function updateUser(id: number, payload: UserAdminWrite): Promise<UserAdminRead> {
  return patch<UserAdminRead>(`/users/${id}`, payload)
}

export async function getUsers(): Promise<UserAdminRead[]> {
  return get<UserAdminRead[]>("/users/")
}

export async function getPublicUsers(): Promise<UserPublicRead[]> {
  return get<UserPublicRead[]>("/users/public")
}
