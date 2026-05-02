import { useState, type SyntheticEvent } from "react"
import { ApiError } from "../../api/http"
import { createOrUpdateReview } from "../../api/reviews"

type ReviewFormProps = {
  bookId: number
  initialRating?: number | null
  initialReviewText?: string | null
  initialAnonymous?: boolean
  onSuccess: () => Promise<void> | void
}

export function ReviewForm({
  bookId,
  initialRating = null,
  initialReviewText = "",
  initialAnonymous = false,
  onSuccess,
}: ReviewFormProps) {
  const [rating, setRating] = useState<string>(
    initialRating !== null ? String(initialRating) : ""
  )
  const [reviewText, setReviewText] = useState(initialReviewText ?? "")
  const [anonymous, setAnonymous] = useState(initialAnonymous)
  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    if (!rating) {
      setErrorMessage("Поставьте оценку")
      return
    }

    const numericRating = Number(rating)

    if (
      Number.isNaN(numericRating) ||
      !Number.isInteger(numericRating) ||
      numericRating < 1 ||
      numericRating > 5
    ) {
      setErrorMessage("Оценка должна быть целым числом от 1 до 5")
      return
    }

    setIsSubmitting(true)

    try {
      await createOrUpdateReview({
        book_id: bookId,
        rating: numericRating,
        anonymous,
        review_text: reviewText || null,
      })

      await onSuccess()
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginTop: 16,
      }}
    >
      <h3 style={{ marginTop: 0 }}>Ваш отзыв</h3>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor={`review-rating-${bookId}`}>Оценка</label>
        <select
          id={`review-rating-${bookId}`}
          value={rating}
          onChange={(event) => setRating(event.target.value)}
          style={{ display: "block", marginTop: 4, padding: 8 }}
        >
          <option value="">Выберите оценку</option>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
          <option value="5">5</option>
        </select>
      </div>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor={`review-text-${bookId}`}>Текст отзыва</label>
        <textarea
          id={`review-text-${bookId}`}
          value={reviewText}
          onChange={(event) => setReviewText(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={anonymous}
            onChange={(event) => setAnonymous(event.target.checked)}
          />
          Отправить анонимно
        </label>
      </div>

      {errorMessage && (
        <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
      )}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Сохраняем..." : "Сохранить отзыв"}
      </button>
    </form>
  )
}