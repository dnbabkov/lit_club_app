import { useNavigate } from "react-router-dom"
import type { BookRead } from "../../types/books"

type BookCardProps = {
  book: BookRead
  canEdit?: boolean
  canAssignUser?: boolean
  canDelete?: boolean
  isDeleting?: boolean
  onEditBook?: (bookId: number) => void
  onAssignUser?: (bookId: number) => void
  onDeleteBook?: (bookId: number) => void
  from?: "/books" | "/books/finished"
}

export function BookCard({
  book,
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

      {(canEdit || canAssignUser || canDelete) && (
        <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
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