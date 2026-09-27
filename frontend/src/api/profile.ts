import {get} from "./http"
import type {UserProfileRead} from "../types/profile"

export async function getMyProfile(): Promise<UserProfileRead> {
  return get<UserProfileRead>("/users/me/profile")
}

export async function getUserProfile(username: string): Promise<UserProfileRead> {
  return get<UserProfileRead>(`/users/${encodeURIComponent(username)}/profile`)
}
