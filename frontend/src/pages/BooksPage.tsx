import { useCallback, useEffect, useState } from "react"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { getBooks } from "../api/books"
import { BookCard } from "../components/books/BookCard"
import { BookCreateForm } from "../components/books/BookCreateForm"
import { BookDescriptionEditor } from "../components/books/BookDescriptionEditor"
import type { BookRead } from "../types/books"

export function BooksPage() {
  const [books, setBooks] = useState<BookRead[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false)
  const [editingBookId, setEditingBookId] = useState<number | null>(null)

  const loadBooksData = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")

    try {
      const response = await getBooks()
      setBooks(response.books)
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadBooksData()
  }, [loadBooksData])

  function handleOpenEditDescription(bookId: number) {
    setEditingBookId(bookId)
  }

  function handleCancelEditDescription() {
    setEditingBookId(null)
  }

  return (
    <Layout>
      <h1>Все книги</h1>

      <div style={{ marginBottom: 24 }}>
        <button
          type="button"
          onClick={() => setIsCreateFormOpen((prev) => !prev)}
        >
          {isCreateFormOpen ? "Скрыть форму" : "Добавить книгу"}
        </button>
      </div>

      {isCreateFormOpen && (
        <BookCreateForm
          onSuccess={async () => {
            setIsCreateFormOpen(false)
            await loadBooksData()
          }}
        />
      )}

      {errorMessage && (
        <p style={{ color: "crimson", marginBottom: 16 }}>{errorMessage}</p>
      )}

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && books.length === 0 && (
        <p>Пока в базе нет ни одной книги.</p>
      )}

      {!isLoading && books.length > 0 && (
        <div>
          {books.map((book) => (
            <div key={book.id}>
              <BookCard
                book={book}
                onEditDescription={handleOpenEditDescription}
                from="/books"
              />

              {editingBookId === book.id && (
                <BookDescriptionEditor
                  bookId={book.id}
                  initialDescription={book.description}
                  onCancel={handleCancelEditDescription}
                  onSuccess={async () => {
                    setEditingBookId(null)
                    await loadBooksData()
                  }}
                />
              )}
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}