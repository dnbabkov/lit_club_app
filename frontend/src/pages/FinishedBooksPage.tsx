import { useCallback, useEffect, useState } from "react"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { getFinishedBooksWithReviews } from "../api/books"
import { BookWithReviewsCard } from "../components/books/BookWithReviewsCard"
import type { BookWithReviewsRead } from "../types/books"

export function FinishedBooksPage() {
  const [items, setItems] = useState<BookWithReviewsRead[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")

  const loadFinishedBooks = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")

    try {
      const data = await getFinishedBooksWithReviews()
      setItems(data)
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
    loadFinishedBooks()
  }, [loadFinishedBooks])

  return (
    <Layout>
      <h1>Прочитанные книги</h1>

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && items.length === 0 && (
        <p>Пока нет ни одной прочитанной книги.</p>
      )}

      {!isLoading && !errorMessage && items.length > 0 && (
        <div>
          {items.map((item) => (
            <BookWithReviewsCard
              key={item.book.id}
              item={item}
            />
          ))}
        </div>
      )}
    </Layout>
  )
}