import type { ReviewRead } from "../../types/reviews"

type ReviewListProps = {
  reviews: ReviewRead[]
}

export function ReviewList({ reviews }: ReviewListProps) {
  if (reviews.length === 0) {
    return <p>Пока нет отзывов.</p>
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {reviews.map((review) => (
        <div
          key={review.id}
          style={{
            border: "1px solid #ddd",
            borderRadius: 8,
            padding: 12,
          }}
        >
          <div style={{ marginBottom: 6, fontWeight: 500 }}>
            {review.username ?? "Anonymous"} — {review.rating}/5
          </div>

          <div style={{ color: "#444" }}>
            {review.review_text?.trim()
              ? review.review_text
              : "Без текста"}
          </div>
        </div>
      ))}
    </div>
  )
}