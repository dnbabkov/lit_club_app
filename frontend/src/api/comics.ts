import { get, uploadFormData, ApiError } from "./http"
import { getToken, reportSessionFailure } from "../auth/token"

export type ComicPage = { id: number; number: number; image_url: string }
export type ComicChapterSummary = {
  id: number
  title: string
  number: number
  is_public: boolean
  cover_url: string | null
  page_count: number
}
export type ComicChapter = ComicChapterSummary & { pages: ComicPage[] }

export const getComicChapters = () => get<ComicChapterSummary[]>("/comics/chapters")
export const getComicChapter = (id: string) => get<ComicChapter>(`/comics/chapters/${id}`)
export const saveComicChapter = (id: number | null, data: FormData) =>
  uploadFormData<ComicChapter>(`/comics/chapters${id === null ? "" : `/${id}`}`, data)

export async function getComicImage(path: string, signal: AbortSignal): Promise<Blob> {
  const token = getToken()
  const response = await fetch(`${import.meta.env.VITE_API_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}, signal,
  })
  if (!response.ok) {
    reportSessionFailure(token, response.status, "Не удалось загрузить изображение")
    throw new ApiError(response.status, "Не удалось загрузить изображение")
  }
  return response.blob()
}
