import { useCallback, useEffect, useMemo, useState } from "react"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { deleteBook, getAllBooksWithReviews, getBooks } from "../api/books"
import { getCurrentUser } from "../api/auth"
import { BookCard } from "../components/books/BookCard"
import { BookCreateForm } from "../components/books/BookCreateForm"
import { BookEditor } from "../components/books/BookEditor"
import { BookAssignUserForm } from "../components/books/BookAssignUserForm"
import type { BookRead, BookWithReviewsRead, CanDeleteBookRead } from "../types/books"
import type { UserRead } from "../api/auth"
import type { ReviewRead } from "../types/reviews.ts"

function bookMatchesSearch(
  book: { title: string; author?: string | null },
  searchQuery: string
): boolean {
  const normalizedSearchQuery = searchQuery.trim().toLowerCase()

  if (!normalizedSearchQuery) {
    return true
  }

  return (
    book.title.toLowerCase().includes(normalizedSearchQuery) ||
    (book.author ?? "").toLowerCase().includes(normalizedSearchQuery)
  )
}

export function BooksPage() {
  const [books, setBooks] = useState<CanDeleteBookRead[]>([])
  const [items, setItems] = useState<BookWithReviewsRead[]>([])
  const [currentUser, setCurrentUser] = useState<UserRead | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [sortField, setSortField] = useState<"default" | "epoch" | "meeting_date" | "rating">("default")
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc")
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
      const data = await getAllBooksWithReviews()
      const booksResponse = await getBooks()
      const userResponse = await getCurrentUser()

      setBooks(booksResponse.books)
      setItems(data)
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

  const averageRatings = useMemo(() => {
    const result = new Map<number, number | null>()
    for (const item of items) {
      result.set(
        item.book.id,
        item.reviews.length
          ? item.reviews.reduce((sum, review) => sum + review.rating, 0) / item.reviews.length
          : null,
      )
    }
    return result
  }, [items])

  const filteredBooks = useMemo(() => {
    const filtered = books.filter((item) => bookMatchesSearch(item.book, searchQuery))
    if (sortField === "default") return filtered

    return [...filtered].sort((left, right) => {
      const leftValue = sortField === "epoch"
        ? left.book.epoch
        : sortField === "meeting_date"
          ? left.book.meeting_date
          : averageRatings.get(left.book.id)
      const rightValue = sortField === "epoch"
        ? right.book.epoch
        : sortField === "meeting_date"
          ? right.book.meeting_date
          : averageRatings.get(right.book.id)

      if ((leftValue === null || leftValue === undefined) && (rightValue === null || rightValue === undefined)) {
        return left.book.id - right.book.id
      }
      if (leftValue === null || leftValue === undefined) return 1
      if (rightValue === null || rightValue === undefined) return -1
      if (leftValue < rightValue) return sortDirection === "asc" ? -1 : 1
      if (leftValue > rightValue) return sortDirection === "asc" ? 1 : -1
      return left.book.id - right.book.id
    })
  }, [averageRatings, books, searchQuery, sortDirection, sortField])

  const randomReviewsByBookId = useMemo(() => {
    const result = new Map<number, ReviewRead | null>()

    for (const item of items) {
      result.set(item.book.id, getRandomReview(item.reviews))
    }

    return result
  }, [items])

  function canEditBook(book: BookRead): boolean {
    return Boolean(
      currentUser &&
        (book.user_id === null || isAdmin || book.user_id === currentUser.id)
    )
  }

  function getRandomReview(reviews: ReviewRead[]): ReviewRead | null {
    if (reviews.length === 0) {
      return null
    }

    const index = Math.floor(Math.random() * reviews.length)
    return reviews[index]
  }

  function canAssignUserToBook(book: BookRead): boolean {
    return Boolean(isAdmin && book.user_id === null)
  }

  function handleOpenEditBook(bookId: number) {
    setEditingBookId((currentBookId) =>
      currentBookId === bookId ? null : bookId
    )
    setAssigningBookId(null)
  }

  function handleCancelEditBook() {
    setEditingBookId(null)
  }

  function handleOpenAssignUser(bookId: number) {
    setAssigningBookId((currentBookId) =>
      currentBookId === bookId ? null : bookId
    )
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
        <input
          type="search"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="Поиск по названию или автору"
          style={{ width: "100%", maxWidth: 480, padding: "10px 12px", marginBottom: 12 }}
        />
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <label htmlFor="books-sort-field">Сортировать:</label>
          <select id="books-sort-field" value={sortField} onChange={(event) => setSortField(event.target.value as typeof sortField)}>
            <option value="default">Без сортировки</option>
            <option value="epoch">По эпохе</option>
            <option value="meeting_date">По дате собрания</option>
            <option value="rating">По средней оценке</option>
          </select>
          {sortField !== "default" && (
            <select aria-label="Направление сортировки" value={sortDirection} onChange={(event) => setSortDirection(event.target.value as typeof sortDirection)}>
              <option value="asc">По возрастанию</option>
              <option value="desc">По убыванию</option>
            </select>
          )}
        </div>
      </div>

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

      {!isLoading && !errorMessage && books.length === 0 && (
        <p>Пока в базе нет ни одной книги.</p>
      )}

      {!isLoading &&
        !errorMessage &&
        books.length > 0 &&
        filteredBooks.length === 0 && <p>По вашему запросу ничего не найдено.</p>}

      {!isLoading && !errorMessage && filteredBooks.length > 0 && (
        <div>
          {filteredBooks.map((item) => {
            const book = item.book

            return (
              <div key={book.id}>
                <BookCard
                  book={book}
                  canEdit={canEditBook(book)}
                  canAssignUser={canAssignUserToBook(book)}
                  canDelete={item.can_delete}
                  isDeleting={deletingBookId === book.id}
                  randomReview={randomReviewsByBookId.get(book.id) ?? null}
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
