import { useState, type SyntheticEvent } from "react"
import { ApiError } from "../../api/http"
import { changeBookDescription, updateBookFields } from "../../api/books"
import type { BookRead } from "../../types/books"

type BookEditorProps = {
  book: BookRead
  onSuccess: () => Promise<void> | void
  onCancel: () => void
}

export function BookEditor({ book, onSuccess, onCancel }: BookEditorProps) {
  const [title, setTitle] = useState(book.title)
  const [author, setAuthor] = useState(book.author)
  const [description, setDescription] = useState(book.description ?? "")
  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const cleanTitle = title.trim()
  const cleanAuthor = author.trim()
  const cleanDescription = description.trim()

  const isTitleChanged = cleanTitle !== book.title.trim()
  const isAuthorChanged = cleanAuthor !== book.author.trim()
  const isDescriptionChanged = cleanDescription !== (book.description ?? "").trim()
  const hasChanges = isTitleChanged || isAuthorChanged || isDescriptionChanged

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    if (!cleanTitle) {
      setErrorMessage("Название не может быть пустым")
      return
    }

    if (!cleanAuthor) {
      setErrorMessage("Автор не может быть пустым")
      return
    }

    if (!hasChanges) {
      setErrorMessage("Нет изменений для сохранения")
      return
    }

    if (isDescriptionChanged && !cleanDescription) {
      setErrorMessage("Описание не может быть пустым")
      return
    }

    setIsSubmitting(true)

    try {
      if (isTitleChanged || isAuthorChanged) {
        await updateBookFields(book.id, {
          title: cleanTitle,
          author: cleanAuthor,
        })
      }

      if (isDescriptionChanged) {
        await changeBookDescription(book.id, {
          description: cleanDescription,
        })
      }

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
        marginBottom: 16,
      }}
    >
      <h3 style={{ marginTop: 0 }}>Редактировать книгу</h3>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor={`book-${book.id}-title`}>Название</label>
        <input
          id={`book-${book.id}-title`}
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor={`book-${book.id}-author`}>Автор</label>
        <input
          id={`book-${book.id}-author`}
          type="text"
          value={author}
          onChange={(event) => setAuthor(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor={`book-${book.id}-description`}>Описание</label>
        <textarea
          id={`book-${book.id}-description`}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        />
      </div>

      {errorMessage && (
        <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
      )}

      <div style={{ display: "flex", gap: 12 }}>
        <button
          type="submit"
          disabled={isSubmitting || !cleanTitle || !cleanAuthor || !hasChanges}
        >
          {isSubmitting ? "Сохраняем..." : "Сохранить"}
        </button>

        <button type="button" onClick={onCancel} disabled={isSubmitting}>
          Отмена
        </button>
      </div>
    </form>
  )
}