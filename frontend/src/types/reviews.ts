export type ReviewRead = {
  id: number
  username: string | null
  book_id: number
  rating: number
  anonymous: boolean
  review_text: string | null
}

export type ReviewCreatePayload = {
  book_id: number
  rating: number
  anonymous: boolean
  review_text: string | null
}