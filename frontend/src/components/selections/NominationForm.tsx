import { useState, type SyntheticEvent } from "react"
import { ApiError } from "../../api/http"
import { createNomination } from "../../api/selections"

type NominationFormProps = {
  selectionId: number
  onSuccess: () => Promise<void> | void
}

export function NominationForm({ selectionId, onSuccess }: NominationFormProps) {
  const [title, setTitle] = useState("")
  const [author, setAuthor] = useState("")
  const [comment, setComment] = useState("")
  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
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
      await createNomination(selectionId, {
        title: cleanTitle,
        author: cleanAuthor,
        comment: cleanComment ? cleanComment : null,
      })

      setTitle("")
      setAuthor("")
      setComment("")
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
    <form onSubmit={handleSubmit} style={{ marginTop: 24 }}>
      <h2>Предложить книгу</h2>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor="nomination-title">Название</label>
        <input
          id="nomination-title"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor="nomination-author">Автор</label>
        <input
          id="nomination-author"
          type="text"
          value={author}
          onChange={(event) => setAuthor(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor="nomination-comment">Комментарий</label>
        <textarea
          id="nomination-comment"
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        />
      </div>

      {errorMessage && (
        <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
      )}

      <button
        type="submit"
        disabled={isSubmitting || !title.trim() || !author.trim()}
      >
        {isSubmitting ? "Отправляем..." : "Предложить"}
      </button>
    </form>
  )
}