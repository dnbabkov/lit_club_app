import { get } from "./http"
import type { UserProfileRead } from "../types/profile"

export async function getMyProfile(): Promise<UserProfileRead> {
  return get<UserProfileRead>("/users/me/profile")
}