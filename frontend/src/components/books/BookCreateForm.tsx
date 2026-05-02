import { useState, type SyntheticEvent } from "react"
import { ApiError } from "../../api/http"
import { createBook } from "../../api/books"

type BookCreateFormProps = {
  onSuccess: () => Promise<void> | void
}

export function BookCreateForm({ onSuccess }: BookCreateFormProps) {
  const [title, setTitle] = useState("")
  const [author, setAuthor] = useState("")
  const [description, setDescription] = useState("")
  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")
    setIsSubmitting(true)

    try {
      await createBook({
        title,
        author,
        description: description || null,
      })

      setTitle("")
      setAuthor("")
      setDescription("")
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
        marginBottom: 24,
      }}
    >
      <h2>Добавить книгу</h2>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor="new-book-title">Название</label>
        <input
          id="new-book-title"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor="new-book-author">Автор</label>
        <input
          id="new-book-author"
          type="text"
          value={author}
          onChange={(event) => setAuthor(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor="new-book-description">Описание</label>
        <textarea
          id="new-book-description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
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
        {isSubmitting ? "Сохранение..." : "Создать книгу"}
      </button>
    </form>
  )
}