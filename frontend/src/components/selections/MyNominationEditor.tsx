import { useState, type SyntheticEvent } from "react"
import { ApiError } from "../../api/http"
import {
  replaceMyNomination,
  updateMyNominationComment,
} from "../../api/selections"
import type { NominationRead } from "../../types/selections"

type MyNominationEditorProps = {
  selectionId: number
  nomination: NominationRead
  onSuccess: () => Promise<void> | void
}

export function MyNominationEditor({
  selectionId,
  nomination,
  onSuccess,
}: MyNominationEditorProps) {
  const [isEditingNomination, setIsEditingNomination] = useState(false)
  const [isEditingComment, setIsEditingComment] = useState(false)

  const [title, setTitle] = useState(nomination.title)
  const [author, setAuthor] = useState(nomination.author)
  const [comment, setComment] = useState(nomination.comment ?? "")

  const [commentOnly, setCommentOnly] = useState(nomination.comment ?? "")

  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleReplaceNomination(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    const cleanTitle = title.trim()
    const cleanAuthor = author.trim()
    const cleanComment = comment.trim()

    if (!cleanTitle || !cleanAuthor) {
      setErrorMessage("Укажите название и автора")
      return
    }

    setIsSubmitting(true)

    try {
      await replaceMyNomination(selectionId, {
        title: cleanTitle,
        author: cleanAuthor,
        comment: cleanComment ? cleanComment : null,
      })

      setIsEditingNomination(false)
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

  async function handleUpdateComment(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    const cleanComment = commentOnly.trim()

    setIsSubmitting(true)

    try {
      await updateMyNominationComment(selectionId, {
        comment: cleanComment ? cleanComment : null,
      })

      setIsEditingComment(false)
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
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginTop: 24,
      }}
    >
      <h2 style={{ marginTop: 0 }}>Моя номинация</h2>

      {!isEditingNomination && !isEditingComment && (
        <>
          <p style={{ margin: "4px 0" }}>
            <strong>{nomination.title}</strong> — {nomination.author}
          </p>

          <p style={{ margin: "4px 0", color: "#555" }}>
            {nomination.comment?.trim() ? nomination.comment : "Комментарий не добавлен"}
          </p>

          <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
            <button type="button" onClick={() => setIsEditingNomination(true)}>
              Изменить номинацию
            </button>

            <button type="button" onClick={() => setIsEditingComment(true)}>
              Изменить комментарий
            </button>
          </div>
        </>
      )}

      {isEditingNomination && (
        <form onSubmit={handleReplaceNomination}>
          <div style={{ marginBottom: 12 }}>
            <label htmlFor="edit-nomination-title">Название</label>
            <input
              id="edit-nomination-title"
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
            />
          </div>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="edit-nomination-author">Автор</label>
            <input
              id="edit-nomination-author"
              type="text"
              value={author}
              onChange={(event) => setAuthor(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
            />
          </div>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="edit-nomination-comment">Комментарий</label>
            <textarea
              id="edit-nomination-comment"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
            />
          </div>

          {errorMessage && (
            <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
          )}

          <div style={{ display: "flex", gap: 12 }}>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim() || !author.trim()}
            >
              {isSubmitting ? "Сохраняем..." : "Сохранить"}
            </button>

            <button
              type="button"
              onClick={() => setIsEditingNomination(false)}
              disabled={isSubmitting}
            >
              Отмена
            </button>
          </div>
        </form>
      )}

      {isEditingComment && (
        <form onSubmit={handleUpdateComment}>
          <div style={{ marginBottom: 12 }}>
            <label htmlFor="edit-comment-only">Комментарий</label>
            <textarea
              id="edit-comment-only"
              value={commentOnly}
              onChange={(event) => setCommentOnly(event.target.value)}
              style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
            />
          </div>

          {errorMessage && (
            <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
          )}

          <div style={{ display: "flex", gap: 12 }}>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Сохраняем..." : "Сохранить комментарий"}
            </button>

            <button
              type="button"
              onClick={() => setIsEditingComment(false)}
              disabled={isSubmitting}
            >
              Отмена
            </button>
          </div>
        </form>
      )}
    </div>
  )
}