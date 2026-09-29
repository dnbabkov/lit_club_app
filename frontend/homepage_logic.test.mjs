import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

const homePage = await readFile(new URL("./src/pages/HomePage.tsx", import.meta.url), "utf8")
const navBar = await readFile(new URL("./src/components/NavBar.tsx", import.meta.url), "utf8")
const router = await readFile(new URL("./src/app/router.tsx", import.meta.url), "utf8")
const booksApi = await readFile(new URL("./src/api/books.ts", import.meta.url), "utf8")
const quotesApi = await readFile(new URL("./src/api/quotes.ts", import.meta.url), "utf8")
const http = await readFile(new URL("./src/api/http.ts", import.meta.url), "utf8")

test("homepage has no visible heading while navigation carries the club brand", () => {
  assert.doesNotMatch(homePage, /<h1>/)
  assert.match(navBar, /<Link to="\/" className="navbar__brand"[\s\S]*>\s*Книжный клуб\s*<\/Link>/)
  assert.doesNotMatch(navBar, /Литературный клуб/)
})

test("homepage keeps the quote attribution link and protected route", () => {
  assert.match(homePage, /<Link to=\{`\/books\/\$\{quote\.book_id\}`\}>/)
  assert.match(homePage, /\{quote\.book_title\}/)
  assert.match(router, /path: "\/",\s*element: \(\s*<ProtectedRoute>\s*<HomePage \/>/s)
})

test("homepage logic handles loading, empty 404, retry, and abort without stale updates", () => {
  assert.match(homePage, /setIsLoading\(true\)/)
  assert.match(homePage, /error instanceof ApiError && error\.status === 404/)
  assert.match(homePage, /Цитат пока нет\./)
  assert.match(homePage, /Повторить/)
  assert.match(homePage, /if \(signal\.aborted\) return/)
  assert.match(homePage, /requestController\.current\?\.abort\(\)/)
  assert.match(homePage, /requestController\.current\?\.abort\(\)\s*\}/)
})

test("random quote API passes AbortSignal through shared HTTP request", () => {
  assert.match(quotesApi, /request<RandomQuoteRead>\("\/quotes\/random", \{ method: "GET", signal \}\)/)
  assert.match(http, /signal\?: AbortSignal/)
  assert.match(http, /signal: options\.signal/)
})

test("year-winners API preserves the authenticated endpoint contract and abort signal", () => {
  assert.match(booksApi, /get<YearWinnerRead\[]>\("\/books\/year-winners", signal\)/)
  assert.match(homePage, /getYearWinners\(controller\.signal\)/)
  assert.match(homePage, /yearWinnersController\.current\?\.abort\(\)/)
})

test("homepage renders year winners above top books with independent states and retry/empty paths", () => {
  const winnersStart = homePage.indexOf('aria-labelledby="year-winners-title"')
  const topBooksStart = homePage.indexOf('aria-labelledby="top-books-title"')
  assert.ok(winnersStart >= 0 && winnersStart < topBooksStart)
  assert.match(homePage, /<h2 id="year-winners-title">Книги года<\/h2>/)
  assert.match(homePage, /\{winner\.start_year\}–\{winner\.start_year \+ 1\}/)
  assert.match(homePage, /<Link to=\{`\/books\/\$\{winner\.id\}`\}>\{winner\.title\}<\/Link>/)
  assert.match(homePage, /<span> — \{winner\.author\}<\/span>/)
  assert.match(homePage, /setYearWinnersError\(true\)/)
  assert.match(homePage, /Не удалось загрузить книги года\./)
  assert.match(homePage, /Книг года пока нет\./)
  assert.match(homePage, /onClick=\{\(\) => void loadYearWinners\(\)\}/)
  assert.match(homePage, /isTopBooksLoading/)
  assert.match(homePage, /topBooksError/)
  assert.match(homePage, /Пока нет оценённых книг\./)
})

test("quote block is centered, fluid within a desktop cap, and wraps long content including attribution", () => {
  assert.match(homePage, /<blockquote style=\{\{ width: "100%", maxWidth: 720, boxSizing: "border-box", margin: "0 auto", textAlign: "center" \}\}>/)
  assert.match(homePage, /<p style=\{\{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" \}\}>/)
  assert.match(homePage, /<footer[^>]*style=\{\{[^}]*overflowWrap: "anywhere"[^}]*\}\}>/)
})
