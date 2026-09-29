import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

const homePage = await readFile(new URL("./src/pages/HomePage.tsx", import.meta.url), "utf8")
const booksApi = await readFile(new URL("./src/api/books.ts", import.meta.url), "utf8")

test("homepage places the top-books heading below the existing quote", () => {
  const quotePosition = homePage.indexOf('<section aria-label="Цитата"')
  const topBooksPosition = homePage.indexOf('<section aria-labelledby="top-books-title"')

  assert.ok(quotePosition >= 0)
  assert.ok(topBooksPosition > quotePosition)
})

test("homepage renders API top books as ranked decimal-rated book links", () => {
  assert.match(booksApi, /get<TopBookRead\[]>\("\/books\/top"\)/)
  assert.match(homePage, /<ol[\s\S]*topBooks\.map\(book =>/)
  assert.match(homePage, /<Link to=\{`\/books\/\$\{book\.id\}`\}>\{book\.title\}<\/Link>/)
  assert.match(homePage, /book\.average_rating\.toFixed\(1\)/)
})

test("homepage separates top-book loading, error retry, and empty states", () => {
  assert.match(homePage, /isTopBooksLoading && <p role="status">Загрузка рейтинга…<\/p>/)
  assert.match(homePage, /Не удалось загрузить рейтинг книг\./)
  assert.match(homePage, /onClick=\{\(\) => void loadTopBooks\(\)\}/)
  assert.match(homePage, /Пока нет оценённых книг\./)
})
