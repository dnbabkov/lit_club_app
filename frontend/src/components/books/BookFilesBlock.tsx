import { useRef, useState } from "react"
import { ApiError } from "../../api/http.ts"
import {
  deleteBookCover,
  deleteBookFile,
  uploadBookCover,
  uploadBookFile,
} from "../../api/books.ts"
import type { BookRead } from "../../types/books.ts"

const API_URL = import.meta.env.VITE_API_URL ?? ""

type BookFilesBlockProps = {
  book: BookRead
  canEditBook: boolean
  onSuccess: () => Promise<void> | void
}

function buildBackendUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path
  }

  return `${API_URL}${path}`
}

function formatFileSize(sizeBytes: number): string {
  if (sizeBytes < 1024) {
    return `${sizeBytes} Б`
  }

  if (sizeBytes < 1024 * 1024) {
    return `${(sizeBytes / 1024).toFixed(1)} КБ`
  }

  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} МБ`
}

export function BookFilesBlock({
  book,
  canEditBook,
  onSuccess,
}: BookFilesBlockProps) {
  const coverInputRef = useRef<HTMLInputElement | null>(null)
  const bookFileInputRef = useRef<HTMLInputElement | null>(null)

  const [errorMessage, setErrorMessage] = useState("")
  const [isUploadingCover, setIsUploadingCover] = useState(false)
  const [isDeletingCover, setIsDeletingCover] = useState(false)
  const [isUploadingBookFile, setIsUploadingBookFile] = useState(false)
  const [isDeletingBookFile, setIsDeletingBookFile] = useState(false)

  const coverSrc = book.cover_url ? buildBackendUrl(book.cover_url) : null
  const downloadHref = book.book_file
    ? buildBackendUrl(book.book_file.download_url)
    : null

  async function handleCoverChange(event: React.ChangeEvent<HTMLInputElement>) {
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
      setIsUploadingCover(false)
    }
  }

  async function handleDeleteCover() {
    setErrorMessage("")
    setIsDeletingCover(true)

    try {
      await deleteBookCover(book.id)
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
      setIsDeletingCover(false)
    }
  }

  async function handleBookFileChange(event: React.ChangeEvent<HTMLInputElement>) {
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
      setIsUploadingBookFile(false)
    }
  }

  async function handleDeleteBookFile() {
    setErrorMessage("")
    setIsDeletingBookFile(true)

    try {
      await deleteBookFile(book.id)
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
      setIsDeletingBookFile(false)
    }
  }

  return (
    <section
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginTop: 16,
      }}
    >
      <h3 style={{ marginTop: 0 }}>Файлы книги</h3>

      <div style={{ display: "flex", gap: 24, alignItems: "flex-start", flexWrap: "wrap" }}>
        <div>
          <h4 style={{ marginTop: 0 }}>Обложка</h4>

          {coverSrc ? (
            <img
              src={coverSrc}
              alt={`Обложка книги ${book.title}`}
              style={{
                display: "block",
                width: 160,
                maxHeight: 240,
                objectFit: "cover",
                borderRadius: 8,
                border: "1px solid #ddd",
              }}
            />
          ) : (
            <p style={{ color: "#666" }}>Обложка не загружена</p>
          )}

          {canEditBook && (
            <div style={{ marginTop: 12 }}>
              <input
                ref={coverInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleCoverChange}
                disabled={isUploadingCover || isDeletingCover}
              />

              {coverSrc && (
                <div style={{ marginTop: 8 }}>
                  <button
                    type="button"
                    onClick={handleDeleteCover}
                    disabled={isUploadingCover || isDeletingCover}
                    style={{ color: "crimson" }}
                  >
                    {isDeletingCover ? "Удаляем..." : "Удалить обложку"}
                  </button>
                </div>
              )}

              {isUploadingCover && <p>Загружаем обложку...</p>}
            </div>
          )}
        </div>

        <div>
          <h4 style={{ marginTop: 0 }}>Файл книги</h4>

          {book.book_file && downloadHref ? (
            <div>
              <p style={{ margin: "4px 0" }}>
                <strong>Файл:</strong>{" "}
                <a href={downloadHref}>
                  {book.book_file.original_filename}
                </a>
              </p>

              <p style={{ margin: "4px 0", color: "#666" }}>
                Размер: {formatFileSize(book.book_file.size_bytes)}
              </p>
            </div>
          ) : (
            <p style={{ color: "#666" }}>Файл книги не загружен</p>
          )}

          {canEditBook && (
            <div style={{ marginTop: 12 }}>
              <input
                ref={bookFileInputRef}
                type="file"
                accept=".fb2,.pdf,.zip"
                onChange={handleBookFileChange}
                disabled={isUploadingBookFile || isDeletingBookFile}
              />

              {book.book_file && (
                <div style={{ marginTop: 8 }}>
                  <button
                    type="button"
                    onClick={handleDeleteBookFile}
                    disabled={isUploadingBookFile || isDeletingBookFile}
                    style={{ color: "crimson" }}
                  >
                    {isDeletingBookFile ? "Удаляем..." : "Удалить файл книги"}
                  </button>
                </div>
              )}

              {isUploadingBookFile && <p>Загружаем файл книги...</p>}
            </div>
          )}
        </div>
      </div>

      {errorMessage && (
        <p style={{ color: "crimson", marginTop: 12 }}>{errorMessage}</p>
      )}
    </section>
  )
}