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
  changeMyNominationToExistingBook,
  changeMyNominationToNewBook,
  updateMyNominationBook,
  updateMyNominationComment,
} from "../../api/selections"
import type { BookRead } from "../../types/books"
import type { NominationRead } from "../../types/selections"

type MyNominationEditorProps = {
  selectionId: number
  nomination: NominationRead
  onSuccess: () => Promise<void> | void
}

type EditMode = "edit-book" | "change-book" | "comment" | null
type ChangeBookMode = "existing" | "new" | null

const buttonTextStyle: CSSProperties = {
  color: "#111",
}

const inputTextStyle: CSSProperties = {
  backgroundColor: "white",
  color: "#111",
}

export function MyNominationEditor({
  selectionId,
  nomination,
  onSuccess,
}: MyNominationEditorProps) {
  const dropdownRef = useRef<HTMLDivElement | null>(null)

  const [editMode, setEditMode] = useState<EditMode>(null)
  const [changeBookMode, setChangeBookMode] = useState<ChangeBookMode>(null)

  const [editBookTitle, setEditBookTitle] = useState(nomination.title)
  const [editBookAuthor, setEditBookAuthor] = useState(nomination.author)

  const [books, setBooks] = useState<BookRead[]>([])
  const [bookSearch, setBookSearch] = useState("")
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null)
  const [isBookDropdownOpen, setIsBookDropdownOpen] = useState(false)
  const [isLoadingBooks, setIsLoadingBooks] = useState(false)

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

  function openEditBookForm() {
    setErrorMessage("")
    setEditBookTitle(nomination.title)
    setEditBookAuthor(nomination.author)
    setEditMode("edit-book")
  }

  function openChangeBookForm() {
    setErrorMessage("")
    setChangeBookMode(null)
    setSelectedBookId(null)
    setBookSearch("")
    setIsBookDropdownOpen(false)
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
    setChangeBookMode(null)
    setSelectedBookId(null)
    setBookSearch("")
    setIsBookDropdownOpen(false)
    setChangeBookTitle("")
    setChangeBookAuthor("")
  }

  function handleBackToChangeBookModeSelection() {
    setChangeBookMode(null)
    setErrorMessage("")
    setSelectedBookId(null)
    setBookSearch("")
    setIsBookDropdownOpen(false)
    setChangeBookTitle("")
    setChangeBookAuthor("")
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

  async function handleChangeToExistingBook(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")

    const selectedBook = books.find((book) => book.id === selectedBookId)

    if (!selectedBook) {
      setErrorMessage("Выберите книгу из базы")
      return
    }

    setIsSubmitting(true)

    try {
      await changeMyNominationToExistingBook(selectionId, {
        book_id: selectedBook.id,
      })

      setEditMode(null)
      setChangeBookMode(null)
      setSelectedBookId(null)
      setBookSearch("")
      await onSuccess()
    } catch (error) {
      handleUnknownError(error)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleChangeToNewBook(event: SyntheticEvent<HTMLFormElement>) {
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
      await changeMyNominationToNewBook(selectionId, {
        title: cleanTitle,
        author: cleanAuthor,
      })

      setEditMode(null)
      setChangeBookMode(null)
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
            {nomination.book_source === "new_book" && (
              <button
                type="button"
                onClick={openEditBookForm}
                style={buttonTextStyle}
              >
                Отредактировать номинацию
              </button>
            )}

            <button
              type="button"
              onClick={openChangeBookForm}
              style={buttonTextStyle}
            >
              Предложить другую книгу
            </button>

            <button
              type="button"
              onClick={openCommentForm}
              style={buttonTextStyle}
            >
              Изменить комментарий
            </button>
          </div>
        </>
      )}

      {editMode === "edit-book" && (
        <form onSubmit={handleEditBook}>
          <h3 style={{ marginTop: 0 }}>Отредактировать номинацию</h3>

          <p style={{ color: "#555" }}>
            Эта форма изменит название и автора книги, которую вы добавили как
            свою. Книги, выбранные из общей базы, так редактировать нельзя.
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
                ...inputTextStyle,
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
                ...inputTextStyle,
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
              style={buttonTextStyle}
            >
              {isSubmitting ? "Сохраняем..." : "Сохранить"}
            </button>

            <button
              type="button"
              onClick={closeForm}
              disabled={isSubmitting}
              style={buttonTextStyle}
            >
              Отмена
            </button>
          </div>
        </form>
      )}

      {editMode === "change-book" && (
        <div>
          <h3 style={{ marginTop: 0 }}>Предложить другую книгу</h3>

          {changeBookMode === null && (
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
                  setChangeBookMode("existing")
                  setErrorMessage("")
                }}
                style={buttonTextStyle}
              >
                Выбрать из базы книг
              </button>

              <button
                type="button"
                onClick={() => {
                  setChangeBookMode("new")
                  setErrorMessage("")
                }}
                style={buttonTextStyle}
              >
                Предложить свою
              </button>

              <button
                type="button"
                onClick={closeForm}
                disabled={isSubmitting}
                style={buttonTextStyle}
              >
                Отмена
              </button>
            </div>
          )}

          {changeBookMode === "existing" && (
            <form onSubmit={handleChangeToExistingBook}>
              <button
                type="button"
                onClick={handleBackToChangeBookModeSelection}
                style={{ marginBottom: 12, color: "#111" }}
              >
                ← Назад
              </button>

              <div
                ref={dropdownRef}
                style={{
                  marginBottom: 12,
                  position: "relative",
                }}
              >
                <label htmlFor="change-book-search">Книга</label>

                <input
                  id="change-book-search"
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
                          <strong style={{ color: "#111" }}>
                            {book.title}
                          </strong>
                          <span style={{ color: "#666" }}>
                            {" "}
                            — {book.author}
                          </span>
                        </button>
                      ))}
                  </div>
                )}
              </div>

              {errorMessage && (
                <p style={{ color: "crimson", marginBottom: 12 }}>
                  {errorMessage}
                </p>
              )}

              <button
                type="submit"
                disabled={isSubmitting || selectedBookId === null}
                style={buttonTextStyle}
              >
                {isSubmitting ? "Сохраняем..." : "Прикрепить книгу"}
              </button>
            </form>
          )}

          {changeBookMode === "new" && (
            <form onSubmit={handleChangeToNewBook}>
              <button
                type="button"
                onClick={handleBackToChangeBookModeSelection}
                style={{ marginBottom: 12, color: "#111" }}
              >
                ← Назад
              </button>

              <div style={{ marginBottom: 12 }}>
                <label htmlFor="change-book-title">
                  Название другой книги
                </label>
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
                    ...inputTextStyle,
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
                    ...inputTextStyle,
                  }}
                />
              </div>

              {errorMessage && (
                <p style={{ color: "crimson", marginBottom: 12 }}>
                  {errorMessage}
                </p>
              )}

              <button
                type="submit"
                disabled={
                  isSubmitting ||
                  !changeBookTitle.trim() ||
                  !changeBookAuthor.trim()
                }
                style={buttonTextStyle}
              >
                {isSubmitting ? "Сохраняем..." : "Прикрепить другую книгу"}
              </button>
            </form>
          )}
        </div>
      )}

      {editMode === "comment" && (
        <form onSubmit={handleUpdateComment}>
          <h3 style={{ marginTop: 0 }}>Изменить комментарий</h3>

          <div style={{ marginBottom: 12 }}>
            <label htmlFor="nomination-comment-only">Комментарий</label>
            <textarea
              id="nomination-comment-only"
              value={commentOnly}
              onChange={(event) => setCommentOnly(event.target.value)}
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

          <div style={{ display: "flex", gap: 12 }}>
            <button
              type="submit"
              disabled={isSubmitting}
              style={buttonTextStyle}
            >
              {isSubmitting ? "Сохраняем..." : "Сохранить комментарий"}
            </button>

            <button
              type="button"
              onClick={closeForm}
              disabled={isSubmitting}
              style={buttonTextStyle}
            >
              Отмена
            </button>
          </div>
        </form>
      )}
    </div>
  )
}