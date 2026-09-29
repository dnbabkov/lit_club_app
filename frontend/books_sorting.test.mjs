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
  { book: { id: 1, title: "Alpha", author: "Author", meeting_date: "2024-01-01" } },
  { book: { id: 2, title: "Beta", author: "Writer", meeting_date: "2025-01-01" } },
  { book: { id: 3, title: "Gamma", author: "Reader", meeting_date: null } },
]

function sortedIds(field, direction, values = new Map()) {
  return [...books]
    .sort((left, right) => compareBooks(left, right, field, direction, values))
    .map((item) => item.book.id)
}

test("meeting date sorts ascending and descending with nulls last", () => {
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
    book: { ...item.book, meeting_date: "2024-01-01" },
  }))
  const ratings = new Map([[1, 3], [2, 3], [3, null]])
  for (const field of ["meeting_date", "rating"]) {
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

test("meeting date descending is the default sort", () => {
  assert.match(source, /useState<"meeting_date" \| "rating">\("meeting_date"\)/)
  assert.match(source, /useState<"asc" \| "desc">\("desc"\)/)
  assert.deepEqual(sortedIds("meeting_date", "desc"), [2, 1, 3])
})

test("epoch is removed from the active sort implementation", () => {
  assert.doesNotMatch(source, /epoch/)
  assert.doesNotMatch(source, /value="default"|value="epoch"/)
})

test("search filtering precedes the default sort", () => {
  const filterIndex = source.indexOf("const filtered = books.filter((item) => bookMatchesSearch(item.book, searchQuery))")
  const sortIndex = source.indexOf("return [...filtered].sort")

  assert.ok(filterIndex >= 0)
  assert.ok(sortIndex > filterIndex)
  assert.match(source, /book\.title\.toLowerCase\(\)\.includes\(normalizedSearchQuery\)/)
  assert.match(source, /\(book\.author \?\? \"\"\)\.toLowerCase\(\)\.includes\(normalizedSearchQuery\)/)
})

test("search and both sorting selectors share a responsive flex row and remain enabled", () => {
  const controlsMatch = source.match(
    /<div style=\{\{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center", marginBottom: 24 \}\}>([\s\S]*?)\n      <\/div>/,
  )
  assert.ok(controlsMatch, "search and sorting controls should have one responsive flex container")

  const controls = controlsMatch[1]
  assert.match(controls, /<input[\s\S]*?type="search"/)
  assert.match(controls, /<select id="books-sort-field"[\s\S]*?<\/select>/)
  assert.match(controls, /<select aria-label="Направление сортировки"[\s\S]*?<\/select>/)
  assert.doesNotMatch(controls, /disabled=/)
  assert.doesNotMatch(controls, /sortField\s*!==\s*"default"|sortField\s*===\s*"default"/)
  assert.match(controls, /<button type="button"[\s\S]*Сортировать[\s\S]*<\/button>/)
})

test("selectors are pending until the explicit sort button is clicked", () => {
  assert.match(source, /useState<"meeting_date" \| "rating">\("meeting_date"\)/g)
  assert.match(source, /useState<"asc" \| "desc">\("desc"\)/g)
  assert.match(
    source,
    /setSortField\(pendingSortField\)[\s\S]*setSortDirection\(pendingSortDirection\)/,
  )
  assert.match(source, /value=\{pendingSortField\}[\s\S]*onChange=/)
  assert.match(source, /value=\{pendingSortDirection\}[\s\S]*onChange=/)
  assert.match(source, /onClick=\{\(\) => \{[\s\S]*setSortField\(pendingSortField\)/)
  assert.match(source, /\}, \[averageRatings, books, searchQuery, sortDirection, sortField\]\)/)
})

test("sort field removes the visible caption but keeps an accessible name", () => {
  assert.doesNotMatch(source, /<label\s+htmlFor="books-sort-field">Сортировать:<\/label>/)
  assert.match(source, /<select id="books-sort-field" aria-label="Сортировать"/)
})
