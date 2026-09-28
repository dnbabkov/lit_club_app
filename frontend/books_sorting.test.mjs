import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

const source = await readFile(new URL("./src/pages/BooksPage.tsx", import.meta.url), "utf8")
const comparatorMatch = source.match(
  /return \[\.\.\.filtered\]\.sort\(\(left, right\) => \{([\s\S]*?)\n    \}\)/,
)
assert.ok(comparatorMatch, "BooksPage sort comparator should remain discoverable")

const compareBooks = new Function(
  "left",
  "right",
  "sortField",
  "sortDirection",
  "averageRatings",
  comparatorMatch[1],
)

const books = [
  { book: { id: 1, title: "Alpha", author: "Author", epoch: "ancient", meeting_date: "2024-01-01" } },
  { book: { id: 2, title: "Beta", author: "Writer", epoch: "modern", meeting_date: "2025-01-01" } },
  { book: { id: 3, title: "Gamma", author: "Reader", epoch: null, meeting_date: null } },
]

function sortedIds(field, direction, values = new Map()) {
  return [...books]
    .sort((left, right) => compareBooks(left, right, field, direction, values))
    .map((item) => item.book.id)
}

test("epoch and meeting date sort ascending and descending with nulls last", () => {
  assert.deepEqual(sortedIds("epoch", "asc"), [1, 2, 3])
  assert.deepEqual(sortedIds("epoch", "desc"), [2, 1, 3])
  assert.deepEqual(sortedIds("meeting_date", "asc"), [1, 2, 3])
  assert.deepEqual(sortedIds("meeting_date", "desc"), [2, 1, 3])
})

test("average rating sort ascending and descending with unrated books last", () => {
  const ratings = new Map([[1, 4], [2, 2], [3, null]])
  assert.deepEqual(sortedIds("rating", "asc", ratings), [2, 1, 3])
  assert.deepEqual(sortedIds("rating", "desc", ratings), [1, 2, 3])
})

test("equal values use book id as a deterministic tie-breaker", () => {
  const tiedBooks = [books[2], books[0], books[1]].map((item) => ({
    book: { ...item.book, epoch: "same", meeting_date: "2024-01-01" },
  }))
  const ratings = new Map([[1, 3], [2, 3], [3, null]])
  for (const field of ["epoch", "meeting_date", "rating"]) {
    const values = field === "rating" ? ratings : new Map()
    for (const direction of ["asc", "desc"]) {
      assert.deepEqual(
        [...tiedBooks].sort((left, right) => compareBooks(left, right, field, direction, values)).map((item) => item.book.id),
        [1, 2, 3],
        `${field} ${direction}`,
      )
    }
  }
})

test("search filtering precedes sorting and default mode preserves filtered order", () => {
  const filterIndex = source.indexOf("const filtered = books.filter((item) => bookMatchesSearch(item.book, searchQuery))")
  const defaultIndex = source.indexOf("if (sortField === \"default\") return filtered")
  const sortIndex = source.indexOf("return [...filtered].sort")

  assert.ok(filterIndex >= 0)
  assert.ok(defaultIndex > filterIndex)
  assert.ok(sortIndex > defaultIndex)
  assert.match(source, /book\.title\.toLowerCase\(\)\.includes\(normalizedSearchQuery\)/)
  assert.match(source, /\(book\.author \?\? \"\"\)\.toLowerCase\(\)\.includes\(normalizedSearchQuery\)/)
})
