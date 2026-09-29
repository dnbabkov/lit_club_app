import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

const readerSource = await readFile(new URL("./src/pages/ComicPage.tsx", import.meta.url), "utf8")
const imageSource = await readFile(new URL("./src/components/ComicImage.tsx", import.meta.url), "utf8")
const cssSource = await readFile(new URL("./src/index.css", import.meta.url), "utf8")

test("the global stylesheet is dark without browser color-scheme switching", () => {
  assert.match(cssSource, /--bg:\s*#16171d/)
  assert.match(cssSource, /color-scheme:\s*dark/)
  assert.doesNotMatch(cssSource, /prefers-color-scheme/)
})

test("comic reader preloads every page and revokes generated URLs during cleanup", () => {
  assert.match(readerSource, /chapter\.pages\.forEach\(page => \{/)
  assert.match(readerSource, /getComicImage\(page\.image_url, controller\.signal\)/)
  assert.match(readerSource, /URL\.createObjectURL\(blob\)/)
  assert.match(readerSource, /createdUrls\.forEach\(url => URL\.revokeObjectURL\(url\)\)/)
  assert.match(readerSource, /controller\.abort\(\)/)
})

test("comic reader keeps navigation and image fallback when a preload is unavailable", () => {
  assert.match(readerSource, /aria-label="Предыдущая страница"/)
  assert.match(readerSource, /aria-label="Следующая страница"/)
  assert.match(readerSource, /preloadedUrl=\{pageImages\[chapter\.pages\[index\]\.image_url\]\}/)
  assert.match(imageSource, /if \(preloadedUrl\) return <img/)
  assert.match(imageSource, /getComicImage\(source, controller\.signal\)/)
  assert.match(imageSource, /Не удалось загрузить изображение\.[\s\S]*Повторить<\/button>/)
})
