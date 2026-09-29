import { useCallback, useEffect, useMemo, useState } from "react"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { getFinishedBooksWithReviews } from "../api/books"
import { BookCard } from "../components/books/BookCard"
import type { BookWithReviewsRead } from "../types/books"
import type { ReviewRead } from "../types/reviews"

function formatAverageRating(reviews: ReviewRead[]): number | null {
  if (reviews.length === 0) {
    return null
  }

  const sum = reviews.reduce((acc, review) => acc + review.rating, 0)
  const average = sum / reviews.length

  return average
}

function getRandomReview(reviews: ReviewRead[]): ReviewRead | null {
  if (reviews.length === 0) {
    return null
  }

  const index = Math.floor(Math.random() * reviews.length)
  return reviews[index]
}

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

export function FinishedBooksPage() {
  const [items, setItems] = useState<BookWithReviewsRead[]>([])
  const [searchQuery, setSearchQuery] = useState("")
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

  const filteredItems = items.filter((item) =>
    bookMatchesSearch(item.book, searchQuery)
  )

  const randomReviewsByBookId = useMemo(() => {
    const result = new Map<number, ReviewRead | null>()

    for (const item of items) {
      result.set(item.book.id, getRandomReview(item.reviews))
    }

    return result
  }, [items])

  return (
    <Layout>
      <h1>Прочитанные книги</h1>

      <input
        type="search"
        value={searchQuery}
        onChange={(event) => setSearchQuery(event.target.value)}
        placeholder="Поиск по названию или автору"
        style={{
          width: "100%",
          maxWidth: 480,
          padding: "10px 12px",
          marginBottom: 24,
        }}
      />

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && items.length === 0 && (
        <p>Пока нет ни одной прочитанной книги.</p>
      )}

      {!isLoading &&
        !errorMessage &&
        items.length > 0 &&
        filteredItems.length === 0 && <p>По вашему запросу ничего не найдено.</p>}

      {!isLoading && !errorMessage && filteredItems.length > 0 && (
        <div>
          {filteredItems.map((item) => (
            <BookCard
              key={item.book.id}
              book={item.book}
              averageRating={formatAverageRating(item.reviews)}
              randomReview={randomReviewsByBookId.get(item.book.id) ?? null}
              from="/books/finished"
            />
          ))}
        </div>
      )}
    </Layout>
  )
}
