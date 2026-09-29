import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

const quoteApi = await readFile(new URL("./src/api/quotes.ts", import.meta.url), "utf8")
const quoteTypes = await readFile(new URL("./src/types/quotes.ts", import.meta.url), "utf8")
const section = await readFile(new URL("./src/components/quotes/QuotesSection.tsx", import.meta.url), "utf8")
const bookPage = await readFile(new URL("./src/pages/BookPage.tsx", import.meta.url), "utf8")

test("quote API exposes book list and CRUD endpoints", () => {
  assert.match(quoteApi, /get<QuoteRead\[\]>\(`\/quotes\/book\/\$\{bookId\}`\)/)
  assert.match(quoteApi, /post<QuoteRead>\("\/quotes\/", payload\)/)
  assert.match(quoteApi, /patch<QuoteRead>\(`\/quotes\/\$\{id\}`, payload\)/)
  assert.match(quoteApi, /del<null>\(`\/quotes\/\$\{id\}`\)/)
  assert.match(quoteTypes, /book_id: number[\s\S]*user_id: number[\s\S]*username: string[\s\S]*text: string/)
})

test("quote loading ignores stale book responses", () => {
  assert.match(section, /let active = true/)
  assert.match(section, /if \(active\) setQuotes\(result\)/)
  assert.match(section, /if \(active\) setError\(errorText\(reason\)\)/)
  assert.match(section, /return \(\) => \{ active = false \}/)
  assert.match(section, /\}, \[bookId\]\)/)
})

test("quote mutations update the cards locally instead of resetting the whole book page", () => {
  assert.match(section, /setQuotes\(previous => \[\.\.\.previous, quote\]\)/)
  assert.match(section, /setQuotes\(previous => previous\.map\(item => item\.id === id \? quote : item\)\)/)
  assert.match(section, /setQuotes\(previous => previous\.filter\(item => item\.id !== quote\.id\)\)/)
  assert.doesNotMatch(section, /loadBookPageData/)
})

test("book detail keeps reviews as the default tab and renders quotes in a separate tab", () => {
  assert.match(bookPage, /useState<"reviews" \| "quotes">\("reviews"\)/)
  assert.match(bookPage, /aria-selected=\{activeTab === "reviews"\}/)
  assert.match(bookPage, /aria-selected=\{activeTab === "quotes"\}/)
  assert.match(bookPage, /activeTab === "quotes" &&[\s\S]*<QuotesSection bookId=\{book\.id\}/)
  assert.match(bookPage, /activeTab === "reviews" &&[\s\S]*<ReviewForm/)
})
