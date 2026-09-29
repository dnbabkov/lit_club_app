import { del, get, patch, post, request } from "./http"
import type { QuoteCreatePayload, QuoteRead, QuoteUpdatePayload, RandomQuoteRead } from "../types/quotes"

export function getQuotesForBook(bookId: number): Promise<QuoteRead[]> {
  return get<QuoteRead[]>(`/quotes/book/${bookId}`)
}

export function getRandomQuote(signal?: AbortSignal): Promise<RandomQuoteRead> {
  return request<RandomQuoteRead>("/quotes/random", { method: "GET", signal })
}

export function createQuote(payload: QuoteCreatePayload): Promise<QuoteRead> {
  return post<QuoteRead>("/quotes/", payload)
}

export function updateQuote(id: number, payload: QuoteUpdatePayload): Promise<QuoteRead> {
  return patch<QuoteRead>(`/quotes/${id}`, payload)
}

export function deleteQuote(id: number): Promise<null> {
  return del<null>(`/quotes/${id}`)
}
