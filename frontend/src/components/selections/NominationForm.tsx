import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type SyntheticEvent,
} from "react"
import { ApiError } from "../../api/http"
import { getBooks } from "../../api/books"
import {
  createNominationFromExistingBook,
  createNominationFromNewBook,
} from "../../api/selections"
import type { BookRead } from "../../types/books"

type NominationFormProps = {
  selectionId: number
  onSuccess: () => Promise<void> | void
}

type NominationMode = "existing" | "new" | null

const buttonTextStyle: CSSProperties = {
  color: "#111",
}

const inputTextStyle: CSSProperties = {
  backgroundColor: "white",
  color: "#111",
}

export function NominationForm({ selectionId, onSuccess }: NominationFormProps) {
  const dropdownRef = useRef<HTMLDivElement | null>(null)

  const [mode, setMode] = useState<NominationMode>(null)

  const [books, setBooks] = useState<BookRead[]>([])
  const [bookSearch, setBookSearch] = useState("")
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null)
  const [isBookDropdownOpen, setIsBookDropdownOpen] = useState(false)

  const [title, setTitle] = useState("")
  const [author, setAuthor] = useState("")
  const [comment, setComment] = useState("")

  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingBooks, setIsLoadingBooks] = useState(false)

  useEffect(() => {
    let isMounted = true

    async function loadBooks() {
      setIsLoadingBooks(true)

      try {
        const response = await getBooks()

        if (!isMounted) {
          return
        }

        setBooks(response.books.map((item) => item.book))
      } catch (error) {
        if (!isMounted) {
          return
        }

        handleUnknownError(error)
      } finally {
        if (isMounted) {
          setIsLoadingBooks(false)
        }
      }
    }

    loadBooks()

    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsBookDropdownOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)

    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  const filteredBooks = useMemo(() => {
    const cleanSearch = bookSearch.trim().toLowerCase()

    if (!cleanSearch) {
      return books
    }

    return books.filter((book) => {
      const bookTitle = book.title.toLowerCase()
      const bookAuthor = book.author.toLowerCase()

      return bookTitle.includes(cleanSearch) || bookAuthor.includes(cleanSearch)
    })
  }, [books, bookSearch])

  function handleUnknownError(error: unknown) {
    if (error instanceof ApiError) {
      setErrorMessage(error.message)
    } else if (error instanceof Error) {
      setErrorMessage(error.message)
    } else {
      setErrorMessage("Unexpected error")
    }
  }

  function handleBackToModeSelection() {
    setMode(null)
    setErrorMessage("")
    setBookSearch("")
    setSelectedBookId(null)
    setIsBookDropdownOpen(false)
    setTitle("")
    setAuthor("")
    setComment("")
  }

  async function handleSubmitExistingBook(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    const selectedBook = books.find((book) => book.id === selectedBookId)
    const cleanComment = comment.trim()

    if (!selectedBook) {
      setErrorMessage("Выберите книгу из базы")
      return
    }

    setIsSubmitting(true)

    try {
      await createNominationFromExistingBook(selectionId, {
        book_id: selectedBook.id,
        comment: cleanComment ? cleanComment : null,
      })

      setSelectedBookId(null)
      setBookSearch("")
      setComment("")
      await onSuccess()
    } catch (error) {
      handleUnknownError(error)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleSubmitNewBook(event: SyntheticEvent<HTMLFormElement>) {
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
      await createNominationFromNewBook(selectionId, {
        title: cleanTitle,
        author: cleanAuthor,
        comment: cleanComment ? cleanComment : null,
      })

      setTitle("")
      setAuthor("")
      setComment("")
      await onSuccess()
    } catch (error) {
      handleUnknownError(error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div style={{ marginTop: 24 }}>
      <h2>Предложить книгу</h2>

      {mode === null && (
        <div
          style={{
            display: "flex",
            gap: 12,
            marginBottom: 16,
            flexWrap: "wrap",
          }}
        >
          <button
            type="button"
            onClick={() => {
              setMode("existing")
              setErrorMessage("")
            }}
            style={buttonTextStyle}
          >
            Выбрать из базы книг
          </button>

          <button
            type="button"
            onClick={() => {
              setMode("new")
              setErrorMessage("")
            }}
            style={buttonTextStyle}
          >
            Предложить свою
          </button>
        </div>
      )}

      {mode === "existing" && (
        <form onSubmit={handleSubmitExistingBook}>
          <button
            type="button"
            onClick={handleBackToModeSelection}
            style={{ marginBottom: 12, color: "#111" }}
          >
            ← Назад
          </button>

          <h3 style={{ marginTop: 0 }}>Выбрать из базы книг</h3>

          <div
            ref={dropdownRef}
            style={{
              marginBottom: 12,
              position: "relative",
            }}
          >
            <label htmlFor="book-search">Книга</label>

            <input
              id="book-search"
              type="text"
              value={bookSearch}
              onFocus={() => setIsBookDropdownOpen(true)}
              onChange={(event) => {
                setBookSearch(event.target.value)
                setSelectedBookId(null)
                setIsBookDropdownOpen(true)
              }}
              placeholder="Начните вводить название или автора"
              disabled={isLoadingBooks}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
                ...inputTextStyle,
              }}
            />

            {isBookDropdownOpen && (
              <div
                style={{
                  position: "absolute",
                  zIndex: 10,
                  left: 0,
                  right: 0,
                  top: "100%",
                  maxHeight: 240,
                  overflowY: "auto",
                  backgroundColor: "white",
                  color: "#111",
                  border: "1px solid #ddd",
                  borderRadius: 6,
                  marginTop: 4,
                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.12)",
                }}
              >
                {isLoadingBooks && (
                  <div style={{ padding: 8, color: "#666" }}>
                    Загружаем книги...
                  </div>
                )}

                {!isLoadingBooks && filteredBooks.length === 0 && (
                  <div style={{ padding: 8, color: "#666" }}>
                    Книг по такому запросу не найдено
                  </div>
                )}

                {!isLoadingBooks &&
                  filteredBooks.map((book) => (
                    <button
                      key={book.id}
                      type="button"
                      onClick={() => {
                        setSelectedBookId(book.id)
                        setBookSearch(`${book.title} — ${book.author}`)
                        setIsBookDropdownOpen(false)
                      }}
                      style={{
                        display: "block",
                        width: "100%",
                        textAlign: "left",
                        padding: 8,
                        border: "none",
                        backgroundColor: "white",
                        color: "#111",
                        cursor: "pointer",
                      }}
                    >
                      <strong style={{ color: "#111" }}>{book.title}</strong>
                      <span style={{ color: "#666" }}> — {book.author}</span>
                    </button>
                  ))}
              </div>
            )}
          </div>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="existing-book-comment">Комментарий</label>
            <textarea
              id="existing-book-comment"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
                ...inputTextStyle,
              }}
            />
          </div>

          {errorMessage && (
            <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
          )}

          <button
            type="submit"
            disabled={isSubmitting || selectedBookId === null}
            style={buttonTextStyle}
          >
            {isSubmitting ? "Отправляем..." : "Предложить"}
          </button>
        </form>
      )}

      {mode === "new" && (
        <form onSubmit={handleSubmitNewBook}>
          <button
            type="button"
            onClick={handleBackToModeSelection}
            style={{ marginBottom: 12, color: "#111" }}
          >
            ← Назад
          </button>

          <h3 style={{ marginTop: 0 }}>Предложить свою книгу</h3>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="nomination-title">Название</label>
            <input
              id="nomination-title"
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
                ...inputTextStyle,
              }}
            />
          </div>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="nomination-author">Автор</label>
            <input
              id="nomination-author"
              type="text"
              value={author}
              onChange={(event) => setAuthor(event.target.value)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
                ...inputTextStyle,
              }}
            />
          </div>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="nomination-comment">Комментарий</label>
            <textarea
              id="nomination-comment"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                marginTop: 4,
                ...inputTextStyle,
              }}
            />
          </div>

          {errorMessage && (
            <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !title.trim() || !author.trim()}
            style={buttonTextStyle}
          >
            {isSubmitting ? "Отправляем..." : "Предложить"}
          </button>
        </form>
      )}
    </div>
  )
}