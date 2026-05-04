export type UserProfileBookRatingRead = {
  username: string | null
  rating: number
}

export type UserProfileBookRead = {
  book_id: number
  title: string
  author: string
  nomination_count: number
  meeting_dates: string[]
  has_won: boolean
  ratings: UserProfileBookRatingRead[]
}

export type UserProfileRead = {
  id: number
  username: string
  telegram_login: string
  role: "member" | "moderator" | "admin"
  nominated_books: UserProfileBookRead[]
}