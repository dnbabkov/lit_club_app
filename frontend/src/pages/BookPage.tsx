import { useCallback, useEffect, useMemo, useState } from "react"
import { useParams } from "react-router-dom"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { getBook } from "../api/books"
import { getMyReviewForBook, getReviewsForBook } from "../api/reviews"
import { ReviewList } from "../components/reviews/ReviewList"
import { ReviewForm } from "../components/reviews/ReviewForm"
import type { BookRead } from "../types/books"
import type { ReviewRead } from "../types/reviews"

function formatAverageRating(reviews: ReviewRead[]): string {
  if (reviews.length === 0) {
    return "Нет оценок"
  }

  const sum = reviews.reduce((acc, review) => acc + review.rating, 0)
  const average = sum / reviews.length

  return `${average.toFixed(1)}/5`
}

export function BookPage() {
  const { bookId } = useParams()

  const [book, setBook] = useState<BookRead | null>(null)
  const [reviews, setReviews] = useState<ReviewRead[]>([])
  const [myReview, setMyReview] = useState<ReviewRead | null>(null)

  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")

  const numericBookId = bookId ? Number(bookId) : null

  const averageRating = useMemo(() => formatAverageRating(reviews), [reviews])

  const loadBookPageData = useCallback(async () => {
    if (!numericBookId || Number.isNaN(numericBookId)) {
      setErrorMessage("Некорректный id книги")
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setErrorMessage("")

    try {
      const bookData = await getBook(numericBookId)
      const reviewsData = await getReviewsForBook(numericBookId)

      let myReviewData: ReviewRead | null = null

      try {
        myReviewData = await getMyReviewForBook(numericBookId)
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          myReviewData = null
        } else {
          throw error
        }
      }

      setBook(bookData)
      setReviews(reviewsData)
      setMyReview(myReviewData)
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
  }, [numericBookId])

  useEffect(() => {
    loadBookPageData()
  }, [loadBookPageData])

  return (
    <Layout>
      <h1>Книга</h1>

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && book && (
        <>
          <div
            style={{
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: 16,
              marginBottom: 24,
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 8 }}>{book.title}</h2>

            <p style={{ margin: "4px 0", color: "#555" }}>
              <strong>Автор:</strong> {book.author}
            </p>

            <p style={{ margin: "4px 0" }}>
              <strong>Средняя оценка:</strong> {averageRating}
            </p>

            <div style={{ marginTop: 12 }}>
              <strong>Описание:</strong>
              <div style={{ marginTop: 4, color: "#444" }}>
                {book.description && book.description.trim().length > 0
                  ? book.description
                  : "Описание пока не добавлено"}
              </div>
            </div>
          </div>

          <ReviewForm
            bookId={book.id}
            initialRating={myReview?.rating ?? null}
            initialReviewText={myReview?.review_text ?? ""}
            initialAnonymous={false}
            onSuccess={loadBookPageData}
          />

          <div style={{ marginTop: 32 }}>
            <h2>Отзывы</h2>
            <ReviewList reviews={reviews} />
          </div>
        </>
      )}
    </Layout>
  )
}