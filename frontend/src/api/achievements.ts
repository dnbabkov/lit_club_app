import { ApiError, get } from "./http"
import { getToken, reportSessionFailure } from "../auth/token"

export type AchievementRead = {
  id: number
  image_url: string
  giver: { id: number; username: string }
}

export const getMyAchievements = () => get<AchievementRead[]>("/users/me/profile/achievements")
export const getUserAchievements = (username: string) =>
  get<AchievementRead[]>(`/users/${encodeURIComponent(username)}/profile/achievements`)

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
