import { useEffect, useState, type SyntheticEvent } from "react"
import { ApiError } from "../../api/http"
import {
  changeMyNominationBook,
  updateMyNominationBook,
  updateMyNominationComment,
} from "../../api/selections"
import type { NominationRead } from "../../types/selections"

type MyNominationEditorProps = {
  selectionId: number
  nomination: NominationRead
  onSuccess: () => Promise<void> | void
}

type EditMode = "edit-book" | "change-book" | "comment" | null

export function MyNominationEditor({
  selectionId,
  nomination,
  onSuccess,
}: MyNominationEditorProps) {
  const [editMode, setEditMode] = useState<EditMode>(null)

  const [editBookTitle, setEditBookTitle] = useState(nomination.title)
  const [editBookAuthor, setEditBookAuthor] = useState(nomination.author)

  const [changeBookTitle, setChangeBookTitle] = useState("")
  const [changeBookAuthor, setChangeBookAuthor] = useState("")

  const [commentOnly, setCommentOnly] = useState(nomination.comment ?? "")

  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    setEditBookTitle(nomination.title)
    setEditBookAuthor(nomination.author)
    setCommentOnly(nomination.comment ?? "")
  }, [nomination.title, nomination.author, nomination.comment])

  function openEditBookForm() {
    setErrorMessage("")
    setEditBookTitle(nomination.title)
    setEditBookAuthor(nomination.author)
    setEditMode("edit-book")
  }

  function openChangeBookForm() {
    setErrorMessage("")
    setChangeBookTitle("")
    setChangeBookAuthor("")
    setEditMode("change-book")
  }

  function openCommentForm() {
    setErrorMessage("")
    setCommentOnly(nomination.comment ?? "")
    setEditMode("comment")
  }

  function closeForm() {
    setErrorMessage("")
    setEditMode(null)
  }

  function handleUnknownError(error: unknown) {
    if (error instanceof ApiError) {
      setErrorMessage(error.message)
    } else if (error instanceof Error) {
      setErrorMessage(error.message)
    } else {
      setErrorMessage("Unexpected error")
    }
  }

  async function handleEditBook(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    const cleanTitle = editBookTitle.trim()
    const cleanAuthor = editBookAuthor.trim()

    if (!cleanTitle || !cleanAuthor) {
      setErrorMessage("Укажите название и автора")
      return
    }

    setIsSubmitting(true)

    try {
      await updateMyNominationBook(selectionId, {
        title: cleanTitle,
        author: cleanAuthor,
      })

      setEditMode(null)
      await onSuccess()
    } catch (error) {
      handleUnknownError(error)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleChangeBook(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    const cleanTitle = changeBookTitle.trim()
    const cleanAuthor = changeBookAuthor.trim()

    if (!cleanTitle || !cleanAuthor) {
      setErrorMessage("Укажите название и автора")
      return
    }

    setIsSubmitting(true)

    try {
      await changeMyNominationBook(selectionId, {
        title: cleanTitle,
        author: cleanAuthor,
      })

      setEditMode(null)
      setChangeBookTitle("")
      setChangeBookAuthor("")
      await onSuccess()
    } catch (error) {
      handleUnknownError(error)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleUpdateComment(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    const cleanComment = commentOnly.trim()

    setIsSubmitting(true)

    try {
      await updateMyNominationComment(selectionId, {
        comment: cleanComment ? cleanComment : null,
      })

      setEditMode(null)
      await onSuccess()
    } catch (error) {
      handleUnknownError(error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginTop: 24,
      }}
    >
      <h2 style={{ marginTop: 0 }}>Моя номинация</h2>

      {editMode === null && (
        <>
          <p style={{ margin: "4px 0" }}>
            <strong>{nomination.title}</strong> — {nomination.author}
          </p>

          <p style={{ margin: "4px 0", color: "#555" }}>
            {nomination.comment?.trim()
              ? nomination.comment
              : "Комментарий не добавлен"}
          </p>

          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 12,
              marginTop: 12,
            }}
          >
            <button type="button" onClick={openEditBookForm}>
              Отредактировать номинацию
            </button>

            <button type="button" onClick={openChangeBookForm}>
              Изменить книгу
            </button>

            <button type="button" onClick={openCommentForm}>
              Изменить комментарий
            </button>
          </div>
        </>
      )}

      {editMode === "edit-book" && (
        <form onSubmit={handleEditBook}>
          <h3 style={{ marginTop: 0 }}>Отредактировать номинацию</h3>

          <p style={{ color: "#555" }}>
            Эта форма изменит название и автора уже связанной с номинацией
            книги.
          </p>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="edit-book-title">Название</label>
            <input
              id="edit-book-title"
              type="text"
              value={editBookTitle}
              onChange={(event) => setEditBookTitle(event.target.value)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
              }}
            />
          </div>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="edit-book-author">Автор</label>
            <input
              id="edit-book-author"
              type="text"
              value={editBookAuthor}
              onChange={(event) => setEditBookAuthor(event.target.value)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
              }}
            />
          </div>

          {errorMessage && (
            <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
          )}

          <div style={{ display: "flex", gap: 12 }}>
            <button
              type="submit"
              disabled={
                isSubmitting || !editBookTitle.trim() || !editBookAuthor.trim()
              }
            >
              {isSubmitting ? "Сохраняем..." : "Сохранить"}
            </button>

            <button type="button" onClick={closeForm} disabled={isSubmitting}>
              Отмена
            </button>
          </div>
        </form>
      )}

      {editMode === "change-book" && (
        <form onSubmit={handleChangeBook}>
          <h3 style={{ marginTop: 0 }}>Изменить книгу</h3>

          <p style={{ color: "#555" }}>
            Эта форма прикрепит к номинации другую книгу. Если такая книга уже
            есть в базе, будет выбрана она. Если её нет, она будет создана.
          </p>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="change-book-title">Название другой книги</label>
            <input
              id="change-book-title"
              type="text"
              value={changeBookTitle}
              onChange={(event) => setChangeBookTitle(event.target.value)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
              }}
            />
          </div>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="change-book-author">Автор другой книги</label>
            <input
              id="change-book-author"
              type="text"
              value={changeBookAuthor}
              onChange={(event) => setChangeBookAuthor(event.target.value)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
              }}
            />
          </div>

          {errorMessage && (
            <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
          )}

          <div style={{ display: "flex", gap: 12 }}>
            <button
              type="submit"
              disabled={
                isSubmitting ||
                !changeBookTitle.trim() ||
                !changeBookAuthor.trim()
              }
            >
              {isSubmitting ? "Сохраняем..." : "Прикрепить другую книгу"}
            </button>

            <button type="button" onClick={closeForm} disabled={isSubmitting}>
              Отмена
            </button>
          </div>
        </form>
      )}

      {editMode === "comment" && (
        <form onSubmit={handleUpdateComment}>
          <h3 style={{ marginTop: 0 }}>Изменить комментарий</h3>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="edit-comment-only">Комментарий</label>
            <textarea
              id="edit-comment-only"
              value={commentOnly}
              onChange={(event) => setCommentOnly(event.target.value)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
              }}
            />
          </div>

          {errorMessage && (
            <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
          )}

          <div style={{ display: "flex", gap: 12 }}>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Сохраняем..." : "Сохранить комментарий"}
            </button>

            <button type="button" onClick={closeForm} disabled={isSubmitting}>
              Отмена
            </button>
          </div>
        </form>
      )}
    </div>
  )
}