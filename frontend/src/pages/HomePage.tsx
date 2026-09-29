import { useCallback, useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import { ApiError } from "../api/http"
import { getTopBooks, getYearWinners } from "../api/books"
import { getRandomQuote } from "../api/quotes"
import { Layout } from "../components/Layout.tsx"
import type { TopBookRead, YearWinnerRead } from "../types/books"
import type { RandomQuoteRead } from "../types/quotes"

export function HomePage() {
  const [topBooks, setTopBooks] = useState<TopBookRead[]>([])
  const [isTopBooksLoading, setIsTopBooksLoading] = useState(true)
  const [topBooksError, setTopBooksError] = useState(false)
  const [yearWinners, setYearWinners] = useState<YearWinnerRead[]>([])
  const [isYearWinnersLoading, setIsYearWinnersLoading] = useState(true)
  const [yearWinnersError, setYearWinnersError] = useState(false)
  const [quote, setQuote] = useState<RandomQuoteRead | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")
  const requestController = useRef<AbortController | null>(null)
  const yearWinnersController = useRef<AbortController | null>(null)

  const loadTopBooks = useCallback(async () => {
    setIsTopBooksLoading(true)
    setTopBooksError(false)
    try {
      setTopBooks(await getTopBooks())
    } catch {
      setTopBooksError(true)
    } finally {
      setIsTopBooksLoading(false)
    }
  }, [])

  const loadYearWinners = useCallback(async () => {
    yearWinnersController.current?.abort()
    const controller = new AbortController()
    yearWinnersController.current = controller
    setIsYearWinnersLoading(true)
    setYearWinnersError(false)
    try {
      const winners = await getYearWinners(controller.signal)
      if (!controller.signal.aborted) setYearWinners(winners)
    } catch {
      if (!controller.signal.aborted) setYearWinnersError(true)
    } finally {
      if (!controller.signal.aborted) setIsYearWinnersLoading(false)
    }
  }, [])

  const loadQuote = useCallback(async () => {
    requestController.current?.abort()
    const controller = new AbortController()
    requestController.current = controller
    const { signal } = controller
    setIsLoading(true)
    setErrorMessage("")

    try {
      const quoteData = await getRandomQuote(signal)
      if (!signal.aborted) setQuote(quoteData)
    } catch (error) {
      if (signal.aborted) return
      if (error instanceof ApiError && error.status === 404) {
        setQuote(null)
        setErrorMessage("Цитат пока нет.")
      } else {
        setErrorMessage("Не удалось загрузить цитату.")
      }
    } finally {
      if (!signal.aborted) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadQuote(), 0)
    return () => {
      window.clearTimeout(timer)
      requestController.current?.abort()
    }
  }, [loadQuote])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadTopBooks(), 0)
    return () => window.clearTimeout(timer)
  }, [loadTopBooks])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadYearWinners(), 0)
    return () => {
      window.clearTimeout(timer)
      yearWinnersController.current?.abort()
    }
  }, [loadYearWinners])

  return (
    <Layout>
      <section aria-label="Цитата" style={{ marginTop: 32 }}>
        {isLoading && <p role="status">Загрузка цитаты…</p>}
        {!isLoading && errorMessage && (
          <>
            <p role="status" aria-live="polite">{errorMessage}</p>
            {errorMessage !== "Цитат пока нет." && (
              <button type="button" onClick={() => {
                void loadQuote()
              }}>
                Повторить
              </button>
            )}
          </>
        )}
        {!isLoading && !errorMessage && quote && (
          <blockquote style={{ width: "100%", maxWidth: 720, boxSizing: "border-box", margin: "0 auto", textAlign: "center" }}>
            <p style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>«{quote.text}»</p>
            <footer style={{ overflowWrap: "anywhere" }}>
              <Link to={`/books/${quote.book_id}`}>
                {quote.book_title}
              </Link>
              <span> — {quote.book_author}</span>
            </footer>
          </blockquote>
        )}
      </section>

      <section aria-labelledby="year-winners-title" style={{ marginTop: 32 }}>
        <h2 id="year-winners-title">Книги года</h2>
        {isYearWinnersLoading && <p role="status">Загрузка книг года…</p>}
        {!isYearWinnersLoading && yearWinnersError && (
          <>
            <p role="status" aria-live="polite">Не удалось загрузить книги года.</p>
            <button type="button" onClick={() => void loadYearWinners()}>Повторить</button>
          </>
        )}
        {!isYearWinnersLoading && !yearWinnersError && yearWinners.length === 0 && (
          <p>Книг года пока нет.</p>
        )}
        {!isYearWinnersLoading && !yearWinnersError && yearWinners.length > 0 && (
          <ul style={{ maxWidth: 720, margin: "0 auto", paddingInlineStart: 28 }}>
            {yearWinners.map(winner => (
              <li key={winner.start_year} style={{ padding: "8px 0", overflowWrap: "anywhere" }}>
                <span>{winner.start_year}–{winner.start_year + 1} </span>
                <Link to={`/books/${winner.id}`}>{winner.title}</Link>
                <span> — {winner.author}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="top-books-title" style={{ marginTop: 32 }}>
        <h2 id="top-books-title">топ книг</h2>
        {isTopBooksLoading && <p role="status">Загрузка рейтинга…</p>}
        {!isTopBooksLoading && topBooksError && (
          <>
            <p role="status" aria-live="polite">Не удалось загрузить рейтинг книг.</p>
            <button type="button" onClick={() => void loadTopBooks()}>Повторить</button>
          </>
        )}
        {!isTopBooksLoading && !topBooksError && topBooks.length === 0 && (
          <p>Пока нет оценённых книг.</p>
        )}
        {!isTopBooksLoading && !topBooksError && topBooks.length > 0 && (
          <ol style={{ maxWidth: 720, margin: "0 auto", paddingInlineStart: 28 }}>
            {topBooks.map(book => (
              <li key={book.id} style={{ padding: "8px 0", overflowWrap: "anywhere" }}>
                <Link to={`/books/${book.id}`}>{book.title}</Link>
                <span> — {book.author}, {book.average_rating.toFixed(1)}</span>
              </li>
            ))}
          </ol>
        )}
      </section>
    </Layout>
  )
}
