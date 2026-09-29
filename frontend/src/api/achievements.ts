import { ApiError, del, get, uploadFormData } from "./http"
import { getToken, reportSessionFailure } from "../auth/token"
import type { UserPublicRead } from "./auth"

export type AchievementRead = {
  id: number
  image_url: string
  giver: { id: number; username: string }
  title: string | null
  description: string | null
}

export const getMyAchievements = (signal?: AbortSignal) => get<AchievementRead[]>("/users/me/profile/achievements", signal)
export const getUserAchievements = (username: string, signal?: AbortSignal) =>
  get<AchievementRead[]>(`/users/${encodeURIComponent(username)}/profile/achievements`, signal)
export const getAchievementDirectory = () => get<UserPublicRead[]>("/users/achievement-directory")

export function createAchievement(recipientId: number, title: string, description: string, image: File) {
  const form = new FormData()
  form.append("recipient_id", String(recipientId))
  form.append("title", title)
  form.append("description", description)
  form.append("image", image)
  return uploadFormData<AchievementRead>("/achievements", form)
}

export const deleteAchievement = (id: number) => del<void>(`/achievements/${id}`)

export async function getAchievementImage(path: string, signal: AbortSignal): Promise<Blob> {
  const token = getToken()
  const response = await fetch(`${import.meta.env.VITE_API_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}, signal,
  })
  if (!response.ok) {
    let message = "Не удалось загрузить ачивку"
    try {
      const data = await response.json()
      if (typeof data.detail === "string") message = data.detail
    } catch { /* Use the default message for non-JSON responses. */ }
    reportSessionFailure(token, response.status, message)
    throw new ApiError(response.status, message)
  }
  return response.blob()
}
