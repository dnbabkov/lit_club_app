export type QuoteRead = {
  id: number
  book_id: number
  user_id: number
  username: string
  text: string
}

export type RandomQuoteRead = {
  book_id: number
  book_title: string
  book_author: string
  text: string
}

export type QuoteCreatePayload = {
  book_id: number
  text: string
}

export type QuoteUpdatePayload = {
  text: string
}
