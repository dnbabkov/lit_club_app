import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { ChangeEvent } from "react"
import { useLocation, useNavigate, useParams } from "react-router-dom"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import {
  deleteBookCover,
  deleteBookFile,
  getBook,
  uploadBookCover,
  uploadBookFile,
} from "../api/books"
import { getCurrentUser } from "../api/auth"
import { getMyReviewForBook, getReviewsForBook } from "../api/reviews"
import { ReviewList } from "../components/reviews/ReviewList"
import { ReviewForm } from "../components/reviews/ReviewForm"
import { BookEditor } from "../components/books/BookEditor"
import { BookAssignUserForm } from "../components/books/BookAssignUserForm"
import type { BookRead } from "../types/books"
import type { ReviewRead } from "../types/reviews"
import type { UserRead } from "../api/auth"

const API_URL = import.meta.env.VITE_API_URL ?? ""

function buildBackendUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path
  }

  return `${API_URL}${path}`
}

function formatAverageRating(reviews: ReviewRead[]): string {
  if (reviews.length === 0) {
    return "Нет оценок"
  }

  const sum = reviews.reduce((acc, review) => acc + review.rating, 0)
  const average = sum / reviews.length

  return `${average.toFixed(1)}/5`
}

export function BookPage() {
  const { bookId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  const from = location.state?.from as "/books" | "/books/finished" | undefined

  const [book, setBook] = useState<BookRead | null>(null)
  const [reviews, setReviews] = useState<ReviewRead[]>([])
  const [myReview, setMyReview] = useState<ReviewRead | null>(null)
  const [currentUser, setCurrentUser] = useState<UserRead | null>(null)

  const [isCreateReviewOpen, setIsCreateReviewOpen] = useState(false)
  const [isEditReviewOpen, setIsEditReviewOpen] = useState(false)
  const [isBookEditorOpen, setIsBookEditorOpen] = useState(false)
  const [isAssignUserFormOpen, setIsAssignUserFormOpen] = useState(false)

  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")

  const [isUploadingCover, setIsUploadingCover] = useState(false)
  const [isDeletingCover, setIsDeletingCover] = useState(false)
  const [isUploadingBookFile, setIsUploadingBookFile] = useState(false)
  const [isDeletingBookFile, setIsDeletingBookFile] = useState(false)

  const coverInputRef = useRef<HTMLInputElement | null>(null)
  const bookFileInputRef = useRef<HTMLInputElement | null>(null)

  const numericBookId = bookId ? Number(bookId) : null

  const averageRating = useMemo(() => formatAverageRating(reviews), [reviews])

  const otherReviews = useMemo(() => {
    if (!myReview) {
      return reviews
    }

    return reviews.filter((review) => review.id !== myReview.id)
  }, [reviews, myReview])

  const isAdmin = currentUser?.role === "admin"

  const canEditBook = Boolean(
    book &&
      currentUser &&
      (book.user_id === null || isAdmin || book.user_id === currentUser.id)
  )

  const canAssignUserToBook = Boolean(book && isAdmin && book.user_id === null)

  const coverSrc = book?.cover_url ? buildBackendUrl(book.cover_url) : null

  const loadBookPageData = useCallback(async () => {
    if (!numericBookId || Number.isNaN(numericBookId)) {
      setErrorMessage("Некорректный id книги")
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setErrorMessage("")

    try {
      const [bookData, reviewsData, userData] = await Promise.all([
        getBook(numericBookId),
        getReviewsForBook(numericBookId),
        getCurrentUser(),
      ])

      let myReviewData: ReviewRead | null = null

      try {
        myReviewData = await getMyReviewForBook(numericBookId)
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          myReviewData = null
        } else {
          throw error
        }
      }

      setBook(bookData)
      setReviews(reviewsData)
      setMyReview(myReviewData)
      setCurrentUser(userData)

      setIsCreateReviewOpen(false)
      setIsEditReviewOpen(false)
      setIsBookEditorOpen(false)
      setIsAssignUserFormOpen(false)
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
  }, [numericBookId])

  useEffect(() => {
    loadBookPageData()
  }, [loadBookPageData])

  function handleOpenBookEditor() {
    setIsBookEditorOpen((prev) => !prev)
    setIsAssignUserFormOpen(false)
  }

  function handleOpenAssignUserForm() {
    setIsAssignUserFormOpen((prev) => !prev)
    setIsBookEditorOpen(false)
  }

  async function handleCoverChange(event: ChangeEvent<HTMLInputElement>) {
    if (!book) {
      return
    }

    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    setErrorMessage("")
    setIsUploadingCover(true)

    try {
      await uploadBookCover(book.id, file)

      if (coverInputRef.current) {
        coverInputRef.current.value = ""
      }

      await loadBookPageData()
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsUploadingCover(false)
    }
  }

  async function handleDeleteCover() {
    if (!book) {
      return
    }

    setErrorMessage("")
    setIsDeletingCover(true)

    try {
      await deleteBookCover(book.id)
      await loadBookPageData()
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsDeletingCover(false)
    }
  }

  async function handleBookFileChange(event: ChangeEvent<HTMLInputElement>) {
    if (!book) {
      return
    }

    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    setErrorMessage("")
    setIsUploadingBookFile(true)

    try {
      await uploadBookFile(book.id, file)

      if (bookFileInputRef.current) {
        bookFileInputRef.current.value = ""
      }

      await loadBookPageData()
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsUploadingBookFile(false)
    }
  }

  async function handleDeleteBookFile() {
    if (!book) {
      return
    }

    setErrorMessage("")
    setIsDeletingBookFile(true)

    try {
      await deleteBookFile(book.id)
      await loadBookPageData()
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsDeletingBookFile(false)
    }
  }

  return (
    <Layout>
      <button
        type="button"
        onClick={() => navigate(from ?? "/books")}
        style={{ marginBottom: 16 }}
      >
        {from === "/books/finished"
          ? "Назад к прочитанным книгам"
          : "Назад к списку книг"}
      </button>

      <h1>Книга</h1>

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && book && (
        <>
          <div
            style={{
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: 16,
              marginBottom: 24,
              display: "flex",
              gap: 24,
              alignItems: "stretch",
              flexWrap: "wrap",
            }}
          >
            <div>
              <div
                style={{
                  width: 180,
                  minWidth: 180,
                  height: 260,
                  borderRadius: 8,
                  overflow: "hidden",
                  backgroundColor: "#ddd",
                  border: "1px solid #ccc",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#777",
                }}
              >
                {coverSrc ? (
                  <img
                    src={coverSrc}
                    alt={`Обложка книги ${book.title}`}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      display: "block",
                    }}
                  />
                ) : (
                  <span>Нет обложки</span>
                )}
              </div>

              {canEditBook && (
                <div style={{ marginTop: 12, width: 180 }}>
                  <input
                    ref={coverInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={handleCoverChange}
                    disabled={isUploadingCover || isDeletingCover}
                    style={{ maxWidth: "100%" }}
                  />

                  {coverSrc && (
                    <button
                      type="button"
                      onClick={handleDeleteCover}
                      disabled={isUploadingCover || isDeletingCover}
                      style={{
                        marginTop: 8,
                        width: "100%",
                        color: "crimson",
                      }}
                    >
                      {isDeletingCover ? "Удаляем..." : "Удалить обложку"}
                    </button>
                  )}

                  {isUploadingCover && (
                    <p style={{ margin: "8px 0 0", color: "#666" }}>
                      Загружаем...
                    </p>
                  )}
                </div>
              )}
            </div>

            <div
              style={{
                flex: 1,
                minWidth: 260,
                minHeight: 260,
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div>
                <h2 style={{ marginTop: 0, marginBottom: 6 }}>
                  {book.title}
                </h2>

                <div
                  style={{
                    fontSize: 18,
                    color: "#555",
                    marginBottom: 12,
                  }}
                >
                  {book.author}
                </div>

                <div style={{ marginBottom: 12 }}>
                  {book.book_file ? (
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ color: "#666", marginRight: 6 }}>
                        Скачать книгу:
                      </span>

                      <a href={buildBackendUrl(book.book_file.download_url)}>
                        {book.book_file.original_filename}
                      </a>
                    </div>
                  ) : (
                    <div style={{ color: "#666", marginBottom: 8 }}>
                      Файл книги не загружен
                    </div>
                  )}

                  {canEditBook && (
                    <div>
                      <input
                        ref={bookFileInputRef}
                        type="file"
                        accept=".fb2,.pdf,.zip"
                        onChange={handleBookFileChange}
                        disabled={isUploadingBookFile || isDeletingBookFile}
                      />

                      {book.book_file && (
                        <button
                          type="button"
                          onClick={handleDeleteBookFile}
                          disabled={isUploadingBookFile || isDeletingBookFile}
                          style={{
                            marginLeft: 8,
                            color: "crimson",
                          }}
                        >
                          {isDeletingBookFile ? "Удаляем..." : "Удалить файл"}
                        </button>
                      )}

                      {isUploadingBookFile && (
                        <p style={{ margin: "8px 0 0", color: "#666" }}>
                          Загружаем файл...
                        </p>
                      )}
                    </div>
                  )}
                </div>

                <p style={{ margin: "4px 0" }}>
                  <strong>Средняя оценка:</strong> {averageRating}
                </p>
              </div>

              <div>
                <strong>Описание:</strong>

                <div style={{ marginTop: 6, color: "#444", lineHeight: 1.5 }}>
                  {book.description && book.description.trim().length > 0
                    ? book.description
                    : "Описание пока не добавлено"}
                </div>

                {(canEditBook || canAssignUserToBook) && (
                  <div
                    style={{
                      display: "flex",
                      gap: 12,
                      marginTop: 16,
                      flexWrap: "wrap",
                    }}
                  >
                    {canEditBook && (
                      <button type="button" onClick={handleOpenBookEditor}>
                        {isBookEditorOpen
                          ? "Скрыть редактор"
                          : "Редактировать книгу"}
                      </button>
                    )}

                    {canAssignUserToBook && (
                      <button type="button" onClick={handleOpenAssignUserForm}>
                        {isAssignUserFormOpen
                          ? "Скрыть назначение пользователя"
                          : "Назначить пользователя"}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {isBookEditorOpen && canEditBook && (
            <BookEditor
              book={book}
              onCancel={() => setIsBookEditorOpen(false)}
              onSuccess={loadBookPageData}
            />
          )}

          {isAssignUserFormOpen && canAssignUserToBook && (
            <BookAssignUserForm
              book={book}
              onCancel={() => setIsAssignUserFormOpen(false)}
              onSuccess={loadBookPageData}
            />
          )}

          <div style={{ marginBottom: 32 }}>
            <h2>Мой отзыв</h2>

            {!myReview && !isCreateReviewOpen && (
              <button type="button" onClick={() => setIsCreateReviewOpen(true)}>
                Оставить отзыв
              </button>
            )}

            {!myReview && isCreateReviewOpen && (
              <ReviewForm
                bookId={book.id}
                initialRating={null}
                initialReviewText=""
                initialAnonymous={false}
                onSuccess={loadBookPageData}
                onCancel={() => setIsCreateReviewOpen(false)}
                title="Оставить отзыв"
                submitLabel="Сохранить отзыв"
              />
            )}

            {myReview && !isEditReviewOpen && (
              <div
                style={{
                  border: "1px solid #ddd",
                  borderRadius: 8,
                  padding: 16,
                  marginTop: 16,
                }}
              >
                <div style={{ marginBottom: 6, fontWeight: 500 }}>
                  {myReview.username ?? "Anonymous"} — {myReview.rating}/5
                </div>

                <div style={{ color: "#444", marginBottom: 12 }}>
                  {myReview.review_text?.trim()
                    ? myReview.review_text
                    : "Без текста"}
                </div>

                <button type="button" onClick={() => setIsEditReviewOpen(true)}>
                  Изменить отзыв
                </button>
              </div>
            )}

            {myReview && isEditReviewOpen && (
              <ReviewForm
                bookId={book.id}
                initialRating={myReview.rating}
                initialReviewText={myReview.review_text ?? ""}
                initialAnonymous={myReview.anonymous ?? false}
                onSuccess={loadBookPageData}
                onCancel={() => setIsEditReviewOpen(false)}
                title="Изменить отзыв"
                submitLabel="Сохранить изменения"
              />
            )}
          </div>

          <div style={{ marginTop: 32 }}>
            <h2>Отзывы</h2>
            <ReviewList reviews={otherReviews} />
          </div>
        </>
      )}
    </Layout>
  )
}