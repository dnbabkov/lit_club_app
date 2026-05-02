import type {ReviewRead} from "./reviews.ts";

export type BookRead = {
  id: number
  title: string
  author: string
  description: string | null
}

export type BookWithReviewsRead = {
  book: BookRead
  reviews: ReviewRead[]
}

export type BooksRead = {
  books: BookRead[]
}

export type BookCreatePayload = {
  title: string
  author: string
  description: string | null
}

export type BookChangeDescriptionPayload = {
  description: string | null
}