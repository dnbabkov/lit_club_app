import { useNavigate } from "react-router-dom"
import type { BookRead } from "../../types/books"
import type { ReviewRead } from "../../types/reviews"

const API_URL = import.meta.env.VITE_API_URL ?? ""

type BookCardProps = {
  book: BookRead
  averageRating?: string | null
  randomReview?: ReviewRead | null
  canEdit?: boolean
  canAssignUser?: boolean
  canDelete?: boolean
  isDeleting?: boolean
  onEditBook?: (bookId: number) => void
  onAssignUser?: (bookId: number) => void
  onDeleteBook?: (bookId: number) => void
  from?: "/books" | "/books/finished"
}

function buildBackendUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path
  }

  return `${API_URL}${path}`
}

export function BookCard({
  book,
  averageRating = null,
  randomReview = null,
  canEdit = false,
  canAssignUser = false,
  canDelete = false,
  isDeleting = false,
  onEditBook,
  onAssignUser,
  onDeleteBook,
  from = "/books",
}: BookCardProps) {
  const navigate = useNavigate()

  const coverSrc = book.cover_url ? buildBackendUrl(book.cover_url) : null

  function handleOpenBookPage() {
    navigate(`/books/${book.id}`, {
      state: { from },
    })
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handleOpenBookPage()
    }
  }

  function handleEditBookClick(event: React.MouseEvent<HTMLButtonElement>) {
    event.stopPropagation()

    if (onEditBook) {
      onEditBook(book.id)
    }
  }

  function handleAssignUserClick(event: React.MouseEvent<HTMLButtonElement>) {
    event.stopPropagation()

    if (onAssignUser) {
      onAssignUser(book.id)
    }
  }

  function handleDeleteBookClick(event: React.MouseEvent<HTMLButtonElement>) {
    event.stopPropagation()

    if (onDeleteBook) {
      onDeleteBook(book.id)
    }
  }

  return (
    <div
      onClick={handleOpenBookPage}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginBottom: 16,
        cursor: "pointer",
      }}
    >
      <div
        style={{
          display: "flex",
          gap: 16,
          alignItems: "flex-start",
        }}
      >
        <div
          style={{
            width: 90,
            minWidth: 90,
            height: 130,
            borderRadius: 6,
            overflow: "hidden",
            backgroundColor: "#ddd",
            border: "1px solid #ccc",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#777",
            fontSize: 12,
            textAlign: "center",
          }}
        >
          {coverSrc ? (
            <img
              src={coverSrc}
              alt={`Обложка книги ${book.title}`}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                display: "block",
              }}
            />
          ) : (
            <span>Нет обложки</span>
          )}
        </div>

        <div
          style={{
            flex: 1,
            minWidth: 0,
            textAlign: "left",
          }}
        >
          <h3 style={{ marginTop: 0, marginBottom: 6 }}>
            {book.title}
          </h3>

          <div
            style={{
              color: "#555",
              marginBottom: averageRating ? 8 : 0,
            }}
          >
            {book.author}
          </div>

          {averageRating && (
            <div style={{ color: "#444" }}>
              <strong>Оценка:</strong> {averageRating}
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: 14 }}>
        {randomReview ? (
          <div
            style={{
              borderTop: "1px solid #eee",
              paddingTop: 12,
              color: "#444",
            }}
          >
            <div style={{ marginBottom: 6, fontWeight: 500 }}>
              Случайный отзыв
            </div>

            <div style={{ lineHeight: 1.45 }}>
              {randomReview.review_text?.trim()
                ? randomReview.review_text
                : "Без текста"}
            </div>

            <div
              style={{
                marginTop: 8,
                color: "#666",
                fontSize: 14,
              }}
            >
              {randomReview.username ?? "Anonymous"} — {randomReview.rating}/5
            </div>
          </div>
        ) : (
          <div
            style={{
              borderTop: "1px solid #eee",
              paddingTop: 12,
              color: "#666",
            }}
          >
            Отзывов пока нет
          </div>
        )}
      </div>

      {(canEdit || canAssignUser || canDelete) && (
        <div
          style={{
            display: "flex",
            gap: 12,
            marginTop: 16,
            flexWrap: "wrap",
          }}
        >
          {canEdit && onEditBook && (
            <button type="button" onClick={handleEditBookClick}>
              Редактировать книгу
            </button>
          )}

          {canAssignUser && onAssignUser && (
            <button type="button" onClick={handleAssignUserClick}>
              Назначить пользователя
            </button>
          )}

          {canDelete && onDeleteBook && (
            <button
              type="button"
              onClick={handleDeleteBookClick}
              disabled={isDeleting}
              style={{ color: "crimson" }}
            >
              {isDeleting ? "Удаляем..." : "Удалить книгу"}
            </button>
          )}
        </div>
      )}
    </div>
  )
}