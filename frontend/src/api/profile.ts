import {get, patch} from "./http"
import type {UpdatePassword, UserProfileRead} from "../types/profile"
import type {UserRead} from "./auth.ts";

export async function getMyProfile(): Promise<UserProfileRead> {
  return get<UserProfileRead>("/users/me/profile")
}

export async function changeMyPassword(
  payload: UpdatePassword
): Promise<UserRead> {
  return patch<UserRead>("/users/me/profile/password", payload)
}