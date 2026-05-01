import { get, patch, post } from "./http"
import type {
  BookChangeDescriptionPayload,
  BookCreatePayload,
  BookRead,
  BooksRead,
  BookWithReviewsRead,
} from "../types/books"

export async function getBooks(): Promise<BooksRead> {
  return get<BooksRead>("/books/")
}

export async function getFinishedBooks(): Promise<BooksRead> {
  return get<BooksRead>("/books/finished")
}

export async function getFinishedBooksWithReviews(): Promise<BookWithReviewsRead[]> {
  return get<BookWithReviewsRead[]>("/books/finished-with-reviews")
}

export async function getBook(bookId: number): Promise<BookRead> {
  return get<BookRead>(`/books/${bookId}`)
}

export async function createBook(payload: BookCreatePayload): Promise<BookRead> {
  return post<BookRead>("/books/", payload)
}

export async function changeBookDescription(
  bookId: number,
  payload: BookChangeDescriptionPayload
): Promise<BookRead> {
  return patch<BookRead>(`/books/${bookId}/description`, payload)
}