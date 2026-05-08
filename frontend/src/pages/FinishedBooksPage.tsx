import { useCallback, useEffect, useState } from "react"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { getFinishedBooksWithReviews } from "../api/books"
import { BookCard } from "../components/books/BookCard"
import type { BookWithReviewsRead } from "../types/books"
import type { ReviewRead } from "../types/reviews"

function formatAverageRating(reviews: ReviewRead[]): string | null {
  if (reviews.length === 0) {
    return null
  }

  const sum = reviews.reduce((acc, review) => acc + review.rating, 0)
  const average = sum / reviews.length

  return `${average.toFixed(1)}/5`
}

function getRandomReview(reviews: ReviewRead[]): ReviewRead | null {
  if (reviews.length === 0) {
    return null
  }

  const index = Math.floor(Math.random() * reviews.length)
  return reviews[index]
}

export function FinishedBooksPage() {
  const [items, setItems] = useState<BookWithReviewsRead[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")

  const loadFinishedBooks = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")

    try {
      const data = await getFinishedBooksWithReviews()
      setItems(data)
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadFinishedBooks()
  }, [loadFinishedBooks])

  return (
    <Layout>
      <h1>Прочитанные книги</h1>

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && items.length === 0 && (
        <p>Пока нет ни одной прочитанной книги.</p>
      )}

      {!isLoading && !errorMessage && items.length > 0 && (
        <div>
          {items.map((item) => (
            <BookCard
              key={item.book.id}
              book={item.book}
              averageRating={formatAverageRating(item.reviews)}
              randomReview={getRandomReview(item.reviews)}
              from="/books/finished"
            />
          ))}
        </div>
      )}
    </Layout>
  )
}