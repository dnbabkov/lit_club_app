import { useCallback, useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate, useParams } from "react-router-dom"
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
  const navigate = useNavigate()
  const location = useLocation()

  const from = location.state?.from as "/books" | "/books/finished" | undefined

  const [book, setBook] = useState<BookRead | null>(null)
  const [reviews, setReviews] = useState<ReviewRead[]>([])
  const [myReview, setMyReview] = useState<ReviewRead | null>(null)

  const [isCreateReviewOpen, setIsCreateReviewOpen] = useState(false)
  const [isEditReviewOpen, setIsEditReviewOpen] = useState(false)

  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")

  const numericBookId = bookId ? Number(bookId) : null

  const averageRating = useMemo(() => formatAverageRating(reviews), [reviews])

  const otherReviews = useMemo(() => {
    if (!myReview) {
      return reviews
    }

    return reviews.filter((review) => review.id !== myReview.id)
  }, [reviews, myReview])

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

      setIsCreateReviewOpen(false)
      setIsEditReviewOpen(false)
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
      <button
        type="button"
        onClick={() => navigate(from ?? "/books")}
        style={{ marginBottom: 16 }}
      >
        {from === "/books/finished"
          ? "Назад к прочитанным книгам"
          : "Назад к списку книг"}
      </button>

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

          <div style={{ marginBottom: 32 }}>
            <h2>Мой отзыв</h2>

            {!myReview && !isCreateReviewOpen && (
              <button type="button" onClick={() => setIsCreateReviewOpen(true)}>
                Оставить отзыв
              </button>
            )}

            {!myReview && isCreateReviewOpen && (
              <ReviewForm
                bookId={book.id}
                initialRating={null}
                initialReviewText=""
                initialAnonymous={false}
                onSuccess={loadBookPageData}
                onCancel={() => setIsCreateReviewOpen(false)}
                title="Оставить отзыв"
                submitLabel="Сохранить отзыв"
              />
            )}

            {myReview && !isEditReviewOpen && (
              <div
                style={{
                  border: "1px solid #ddd",
                  borderRadius: 8,
                  padding: 16,
                  marginTop: 16,
                }}
              >
                <div style={{ marginBottom: 6, fontWeight: 500 }}>
                  {myReview.username ?? "Anonymous"} — {myReview.rating}/5
                </div>

                <div style={{ color: "#444", marginBottom: 12 }}>
                  {myReview.review_text?.trim()
                    ? myReview.review_text
                    : "Без текста"}
                </div>

                <button type="button" onClick={() => setIsEditReviewOpen(true)}>
                  Изменить отзыв
                </button>
              </div>
            )}

            {myReview && isEditReviewOpen && (
              <ReviewForm
                bookId={book.id}
                initialRating={myReview.rating}
                initialReviewText={myReview.review_text ?? ""}
                initialAnonymous={myReview.anonymous ?? false}
                onSuccess={loadBookPageData}
                onCancel={() => setIsEditReviewOpen(false)}
                title="Изменить отзыв"
                submitLabel="Сохранить изменения"
              />
            )}
          </div>

          <div style={{ marginTop: 32 }}>
            <h2>Отзывы</h2>
            <ReviewList reviews={otherReviews} />
          </div>
        </>
      )}
    </Layout>
  )
}