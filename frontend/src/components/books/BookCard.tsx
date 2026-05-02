import type { BookRead } from "../../types/books"

type BookCardProps = {
  book: BookRead
  onEditDescription?: (bookId: number) => void
}

export function BookCard({ book, onEditDescription }: BookCardProps) {
  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginBottom: 16,
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: 8 }}>{book.title}</h3>

      <p style={{ margin: "4px 0", color: "#555" }}>
        <strong>Автор:</strong> {book.author}
      </p>

      <div style={{ marginTop: 12 }}>
        <strong>Описание:</strong>
        <div style={{ marginTop: 4, color: "#444" }}>
          {book.description && book.description.trim().length > 0
            ? book.description
            : "Описание пока не добавлено"}
        </div>
      </div>

      {onEditDescription && (
        <div style={{ marginTop: 16 }}>
          <button type="button" onClick={() => onEditDescription(book.id)}>
            Изменить описание
          </button>
        </div>
      )}
    </div>
  )
}