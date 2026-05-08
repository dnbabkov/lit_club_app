import type {ReviewRead} from "./reviews.ts";

export type BookRead = {
  id: number
  title: string
  author: string
  description: string | null
  user_id: number | null

  cover_url: string | null
  book_file: BookFileRead | null
}

export type BookFileRead = {
  id: number
  original_filename: string
  content_type: string
  size_bytes: number
  download_url: string
}

export type CanDeleteBookRead = {
  book: BookRead
  can_delete: boolean
}

export type BookWithReviewsRead = {
  book: BookRead
  reviews: ReviewRead[]
}

export type BooksRead = {
  books: CanDeleteBookRead[]
}

export type BookCreatePayload = {
  title: string
  author: string
  description: string | null
}

export type BookChangeDescriptionPayload = {
  description: string
}

export type BookUpdateFieldsPayload = {
  title: string
  author: string
}

export type BookAssignUserPayload = {
  user_id: number
}