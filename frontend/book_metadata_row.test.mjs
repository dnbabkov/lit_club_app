import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

const componentSource = await readFile(
  new URL("./src/components/books/BookMetadataRow.tsx", import.meta.url),
  "utf8",
)
const cardSource = await readFile(
  new URL("./src/components/books/BookCard.tsx", import.meta.url),
  "utf8",
)
const listSource = await readFile(
  new URL("./src/pages/BooksPage.tsx", import.meta.url),
  "utf8",
)
const detailSource = await readFile(
  new URL("./src/pages/BookPage.tsx", import.meta.url),
  "utf8",
)

function loadFormatter(name) {
  const match = componentSource.match(
    new RegExp(`function ${name}\\([^)]*\\): string \\{[\\s\\S]*?\\n\\}`),
  )
  assert.ok(match, `${name} should remain a local formatter`)
  const javascriptFunction = match[0]
    .replace("): string", ")")
    .replace(/([,(]\s*[A-Za-z_$][\w$]*)\s*:\s*[^,\)]+/g, "$1")
  return new Function(`${javascriptFunction}; return ${name}`)()
}

test("meeting date formatting is calendar-date and timezone safe", () => {
  const formatMeetingDate = loadFormatter("formatMeetingDate")

  assert.equal(formatMeetingDate(null), "—")
  assert.equal(formatMeetingDate(""), "—")
  assert.equal(formatMeetingDate("2024-02-29T23:30:00-05:00"), "29.02.2024")
  assert.equal(formatMeetingDate("2024-02-29"), "29.02.2024")
})

test("average rating formatting preserves zero and uses one decimal", () => {
  const formatAverageRating = loadFormatter("formatAverageRating")

  assert.equal(formatAverageRating(null), "—")
  assert.equal(formatAverageRating(0), "0.0")
  assert.equal(formatAverageRating(4), "4.0")
  assert.equal(formatAverageRating(4.25), "4.3")
})

test("the shared row has both required labels and is rendered below descriptions", () => {
  assert.match(componentSource, /<strong>Дата собрания:<\/strong>\s*\{formatMeetingDate\(meetingDate\)\}/)
  assert.match(componentSource, /<strong>Средний балл:<\/strong>\s*\{formatAverageRating\(averageRating\)\}/)

  const cardDescription = cardSource.indexOf("Описание пока не добавлено")
  const cardMetadata = cardSource.indexOf("<BookMetadataRow")
  assert.ok(cardDescription >= 0 && cardMetadata > cardDescription)

  const detailDescription = detailSource.indexOf("Описание пока не добавлено")
  const detailMetadata = detailSource.indexOf("<BookMetadataRow")
  assert.ok(detailDescription >= 0 && detailMetadata > detailDescription)
})

test("Books list renders cards that use the shared metadata row", () => {
  assert.match(listSource, /<BookCard[\s\S]*averageRating=\{averageRatings\.get\(book\.id\) \?\? null\}/)
  assert.match(cardSource, /import \{ BookMetadataRow \} from "\.\/BookMetadataRow"/)
  assert.match(detailSource, /import \{ BookMetadataRow \} from "\.\.\/components\/books\/BookMetadataRow"/)
})

test("card keyboard activation ignores interactive descendants", () => {
  assert.match(
    cardSource,
    /event\.target instanceof Element[\s\S]*?closest\("button, a, input, select, textarea, \[role=\\"button\\"\]"\)/,
  )
  assert.match(cardSource, /interactiveDescendant !== event\.currentTarget[\s\S]*?return/)
})
