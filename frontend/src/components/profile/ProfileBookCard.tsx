import type { UserProfileBookRead } from "../../types/profile"

type ProfileBookCardProps = {
  item: UserProfileBookRead
}

function formatMeetingDate(value: string): string {
  if (value === "Дата не назначена") {
    return value
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString("ru-RU", {
    year: "numeric",
    month: "long",
    day: "numeric",
  })
}

export function ProfileBookCard({ item }: ProfileBookCardProps) {
  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginBottom: 16,
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: 8 }}>{item.title}</h3>

      <p style={{ margin: "4px 0", color: "#555" }}>
        <strong>Автор:</strong> {item.author}
      </p>

      <p style={{ margin: "4px 0" }}>
        <strong>Предлагалась:</strong> {item.nomination_count} раз
      </p>

      <p style={{ margin: "4px 0" }}>
        <strong>Статус:</strong>{" "}
        {item.has_won ? "Книга побеждала" : "Книга не побеждала"}
      </p>

      <div style={{ marginTop: 12 }}>
        <strong>На каких встречах:</strong>
        {item.meeting_dates.length > 0 ? (
          <ul style={{ marginTop: 6, paddingLeft: 20 }}>
            {item.meeting_dates.map((date, index) => (
              <li key={`${item.book_id}-${index}`}>{formatMeetingDate(date)}</li>
            ))}
          </ul>
        ) : (
          <div style={{ marginTop: 6, color: "#777" }}>Нет данных</div>
        )}
      </div>

      <div style={{ marginTop: 12 }}>
        <strong>Оценки пользователей:</strong>
        {item.ratings.length > 0 ? (
          <ul style={{ marginTop: 6, paddingLeft: 20 }}>
            {item.ratings.map((rating, index) => (
              <li key={`${item.book_id}-rating-${index}`}>
                {rating.username ?? "Anonymous"} — {rating.rating}/5
              </li>
            ))}
          </ul>
        ) : (
          <div style={{ marginTop: 6, color: "#777" }}>
            Оценок пока нет
          </div>
        )}
      </div>
    </div>
  )
}