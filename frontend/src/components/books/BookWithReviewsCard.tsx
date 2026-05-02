import { useMemo } from "react"
import { useNavigate } from "react-router-dom"
import type { BookWithReviewsRead } from "../../types/books"

type BookWithReviewsCardProps = {
  item: BookWithReviewsRead
}

function getAverageRating(ratings: number[]): string {
  if (ratings.length === 0) {
    return "Нет оценок"
  }

  const sum = ratings.reduce((acc, value) => acc + value, 0)
  const average = sum / ratings.length

  return `${average.toFixed(1)}/5`
}

export function BookWithReviewsCard({ item }: BookWithReviewsCardProps) {
  const navigate = useNavigate()
  const { book, reviews } = item

  const averageRating = useMemo(
    () => getAverageRating(reviews.map((review) => review.rating)),
    [reviews]
  )

  const previewReview = useMemo(() => {
    if (reviews.length === 0) {
      return null
    }

    const randomIndex = Math.floor(Math.random() * reviews.length)
    return reviews[randomIndex]
  }, [reviews])

  function handleOpenBookPage() {
    navigate(`/books/${book.id}`, {
      state: { from: "/books/finished" },
    })
  }

  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginBottom: 16,
        cursor: "pointer",
      }}
      onClick={handleOpenBookPage}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handleOpenBookPage()
        }
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: 8 }}>{book.title}</h3>

      <p style={{ margin: "4px 0", color: "#555" }}>
        <strong>Автор:</strong> {book.author}
      </p>

      <p style={{ margin: "4px 0" }}>
        <strong>Оценка:</strong> {averageRating}
      </p>

      <div style={{ marginTop: 12 }}>
        <strong>Отзыв:</strong>

        {previewReview ? (
          <div
            style={{
              marginTop: 8,
              padding: 12,
              background: "#f8f8f8",
              borderRadius: 8,
            }}
          >
            <div style={{ marginBottom: 6, fontWeight: 500 }}>
              {previewReview.username ?? "Anonymous"} — {previewReview.rating}/5
            </div>

            <div style={{ color: "#444" }}>
              {previewReview.review_text?.trim()
                ? previewReview.review_text
                : "Без текста"}
            </div>
          </div>
        ) : (
          <div style={{ marginTop: 8, color: "#777" }}>
            Пока нет отзывов
          </div>
        )}
      </div>
    </div>
  )
}