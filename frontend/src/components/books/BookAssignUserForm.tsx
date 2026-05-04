import { useEffect, useState, type SyntheticEvent } from "react"
import { ApiError } from "../../api/http"
import { assignUserToBook } from "../../api/books"
import { getUsers } from "../../api/auth"
import type { UserRead } from "../../api/auth"
import type { BookRead } from "../../types/books"

type BookAssignUserFormProps = {
  book: BookRead
  onSuccess: () => Promise<void> | void
  onCancel: () => void
}

export function BookAssignUserForm({
  book,
  onSuccess,
  onCancel,
}: BookAssignUserFormProps) {
  const [users, setUsers] = useState<UserRead[]>([])
  const [userId, setUserId] = useState("")
  const [errorMessage, setErrorMessage] = useState("")
  const [isLoadingUsers, setIsLoadingUsers] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    async function loadUsers() {
      setIsLoadingUsers(true)
      setErrorMessage("")

      try {
        const response = await getUsers()
        setUsers(response)
      } catch (error) {
        if (error instanceof ApiError) {
          setErrorMessage(error.message)
        } else if (error instanceof Error) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage("Unexpected error")
        }
      } finally {
        setIsLoadingUsers(false)
      }
    }

    loadUsers()
  }, [])

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    const parsedUserId = Number(userId)

    if (!Number.isInteger(parsedUserId) || parsedUserId <= 0) {
      setErrorMessage("Выберите пользователя")
      return
    }

    setIsSubmitting(true)

    try {
      await assignUserToBook(book.id, {
        user_id: parsedUserId,
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
      <h3 style={{ marginTop: 0 }}>Назначить пользователя книге</h3>

      <p style={{ marginTop: 0, color: "#555" }}>
        Книга: <strong>{book.title}</strong>
      </p>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor={`book-${book.id}-assign-user`}>Пользователь</label>

        <select
          id={`book-${book.id}-assign-user`}
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          disabled={isLoadingUsers || isSubmitting}
          style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
        >
          <option value="">
            {isLoadingUsers ? "Загружаем пользователей..." : "Выберите пользователя"}
          </option>

          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.username}
            </option>
          ))}
        </select>
      </div>

      {!isLoadingUsers && users.length === 0 && !errorMessage && (
        <p style={{ color: "#555", marginBottom: 12 }}>
          Пользователи не найдены
        </p>
      )}

      {errorMessage && (
        <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
      )}

      <div style={{ display: "flex", gap: 12 }}>
        <button
          type="submit"
          disabled={isSubmitting || isLoadingUsers || !userId}
        >
          {isSubmitting ? "Назначаем..." : "Назначить"}
        </button>

        <button type="button" onClick={onCancel} disabled={isSubmitting}>
          Отмена
        </button>
      </div>
    </form>
  )
}