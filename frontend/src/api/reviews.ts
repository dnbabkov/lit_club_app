import { get, post } from "./http"
import type { ReviewCreatePayload, ReviewRead } from "../types/reviews"

export async function createOrUpdateReview(
  payload: ReviewCreatePayload
): Promise<ReviewRead> {
  return post<ReviewRead>("/reviews/", payload)
}

export async function getMyReviewForBook(bookId: number): Promise<ReviewRead> {
  return get<ReviewRead>(`/reviews/book/${bookId}`)
}

export async function getReviewsForBook(bookId: number): Promise<ReviewRead[]> {
  return get<ReviewRead[]>(`/books/${bookId}/reviews`)
}