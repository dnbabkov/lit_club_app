import { useState, type SyntheticEvent } from "react"
import { ApiError } from "../../api/http"
import { changeBookDescription } from "../../api/books"

type BookDescriptionEditorProps = {
  bookId: number
  initialDescription: string | null
  onSuccess: () => Promise<void> | void
  onCancel: () => void
}

export function BookDescriptionEditor({
  bookId,
  initialDescription,
  onSuccess,
  onCancel,
}: BookDescriptionEditorProps) {
  const [description, setDescription] = useState(initialDescription ?? "")
  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")
    setIsSubmitting(true)

    try {
      await changeBookDescription(bookId, {
        description,
      })

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
      <h3>Изменить описание</h3>

      <div style={{ marginBottom: 12 }}>
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          style={{ display: "block", width: "100%", padding: 8 }}
        />
      </div>

      {errorMessage && (
        <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
      )}

      <div style={{ display: "flex", gap: 12 }}>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Сохраняем..." : "Сохранить"}
        </button>

        <button type="button" onClick={onCancel} disabled={isSubmitting}>
          Отмена
        </button>
      </div>
    </form>
  )
}