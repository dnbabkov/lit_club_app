import {del, get, patch, post, uploadFormData} from "./http"
import type {
  BookAssignUserPayload,
  BookChangeDescriptionPayload,
  BookCreatePayload,
  BookRead,
  BooksRead, BookUpdateFieldsPayload,
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

export async function updateBookFields(
  bookId: number,
  payload: BookUpdateFieldsPayload
): Promise<BookRead> {
  const searchParams = new URLSearchParams({
    title: payload.title,
    author: payload.author,
  })

  return patch<BookRead>(`/books/${bookId}?${searchParams.toString()}`, {})
}

export async function assignUserToBook(
  bookId: number,
  payload: BookAssignUserPayload
): Promise<BookRead> {
  return patch<BookRead>(`/books/${bookId}/user`, payload)
}

export async function deleteBook(bookId: number): Promise<void> {
  return del<void>(`/books/${bookId}`)
}

export async function uploadBookCover(bookId: number, file: File): Promise<BookRead> {
  const formData = new FormData()
  formData.append("file", file)

  return uploadFormData<BookRead>(`/books/${bookId}/cover`, formData)
}

export async function deleteBookCover(bookId: number): Promise<BookRead> {
  return del<BookRead>(`/books/${bookId}/cover`)
}

export async function uploadBookFile(bookId: number, file: File): Promise<BookRead> {
  const formData = new FormData()
  formData.append("file", file)

  return uploadFormData<BookRead>(`/books/${bookId}/file`, formData)
}

export async function deleteBookFile(bookId: number): Promise<BookRead> {
  return del<BookRead>(`/books/${bookId}/file`)
}