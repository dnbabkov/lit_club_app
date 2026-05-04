import { useCallback, useEffect, useState } from "react"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { deleteBook, getBooks } from "../api/books"
import { getCurrentUser } from "../api/auth"
import { BookCard } from "../components/books/BookCard"
import { BookCreateForm } from "../components/books/BookCreateForm"
import { BookEditor } from "../components/books/BookEditor"
import { BookAssignUserForm } from "../components/books/BookAssignUserForm"
import type { BookRead, CanDeleteBookRead } from "../types/books"
import type { UserRead } from "../api/auth"

export function BooksPage() {
  const [books, setBooks] = useState<CanDeleteBookRead[]>([])
  const [currentUser, setCurrentUser] = useState<UserRead | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false)
  const [editingBookId, setEditingBookId] = useState<number | null>(null)
  const [assigningBookId, setAssigningBookId] = useState<number | null>(null)
  const [deletingBookId, setDeletingBookId] = useState<number | null>(null)

  const loadBooksData = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")

    try {
      const booksResponse = await getBooks()
      const userResponse = await getCurrentUser()

      setBooks(booksResponse.books)
      setCurrentUser(userResponse)
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

  const isAdmin = currentUser?.role === "admin"

  function canEditBook(book: BookRead): boolean {
    return Boolean(
      currentUser &&
        (book.user_id === null || isAdmin || book.user_id === currentUser.id)
    )
  }

  function canAssignUserToBook(book: BookRead): boolean {
    return Boolean(isAdmin && book.user_id === null)
  }

  function handleOpenEditBook(bookId: number) {
    setEditingBookId((currentBookId) => (currentBookId === bookId ? null : bookId))
    setAssigningBookId(null)
  }

  function handleCancelEditBook() {
    setEditingBookId(null)
  }

  function handleOpenAssignUser(bookId: number) {
    setAssigningBookId((currentBookId) => (currentBookId === bookId ? null : bookId))
    setEditingBookId(null)
  }

  function handleCancelAssignUser() {
    setAssigningBookId(null)
  }

  async function handleDeleteBook(bookId: number) {
    const item = books.find((entry) => entry.book.id === bookId)

    if (!item) {
      return
    }

    const confirmed = window.confirm(
      `Удалить книгу "${item.book.title}"? Это действие нельзя отменить.`
    )

    if (!confirmed) {
      return
    }

    setDeletingBookId(bookId)
    setErrorMessage("")

    try {
      await deleteBook(bookId)

      if (editingBookId === bookId) {
        setEditingBookId(null)
      }

      if (assigningBookId === bookId) {
        setAssigningBookId(null)
      }

      await loadBooksData()
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setDeletingBookId(null)
    }
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
          {books.map((item) => {
            const book = item.book

            return (
              <div key={book.id}>
                <BookCard
                  book={book}
                  canEdit={canEditBook(book)}
                  canAssignUser={canAssignUserToBook(book)}
                  canDelete={item.can_delete}
                  isDeleting={deletingBookId === book.id}
                  onEditBook={handleOpenEditBook}
                  onAssignUser={handleOpenAssignUser}
                  onDeleteBook={handleDeleteBook}
                  from="/books"
                />

                {editingBookId === book.id && canEditBook(book) && (
                  <BookEditor
                    book={book}
                    onCancel={handleCancelEditBook}
                    onSuccess={async () => {
                      setEditingBookId(null)
                      await loadBooksData()
                    }}
                  />
                )}

                {assigningBookId === book.id && canAssignUserToBook(book) && (
                  <BookAssignUserForm
                    book={book}
                    onCancel={handleCancelAssignUser}
                    onSuccess={async () => {
                      setAssigningBookId(null)
                      await loadBooksData()
                    }}
                  />
                )}
              </div>
            )
          })}
        </div>
      )}
    </Layout>
  )
}