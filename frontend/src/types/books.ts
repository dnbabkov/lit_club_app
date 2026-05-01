export type BookRead = {
  id: number
  title: string
  author: string
  description: string | null
}

export type ReviewRead = {
  id: number
  username: string | null
  book_id: number
  rating: number
  review_text: string | null
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