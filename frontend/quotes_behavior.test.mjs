import assert from "node:assert/strict"
import { execFile, spawn } from "node:child_process"
import { promisify } from "node:util"
import { test } from "node:test"

const run = promisify(execFile)

function pageSource(port) {
  return `<!doctype html><meta charset="utf-8"><div id="root"></div><pre id="result">running</pre>
<script type="module">
const gets = new Map()
const requests = []
let postCount = 0
let nextId = 1
window.fetch = async (input, init = {}) => {
  const path = String(input)
  const method = init.method || "GET"
  requests.push({ path, method })
  if (method === "GET") {
    const bookId = Number(path.split("/").pop())
    return new Promise((resolve, reject) => gets.set(bookId, { resolve, reject }))
  }
  if (method === "POST") {
    postCount++
    const payload = JSON.parse(init.body)
    return { ok: true, status: 201, json: async () => ({ id: nextId++, book_id: payload.book_id, user_id: 7, username: "reader", text: payload.text }) }
  }
  throw new Error("unexpected request")
}
window.confirm = () => true
const response = (value, status = 200) => ({ ok: status < 400, status, json: async () => value })
const wait = (milliseconds = 0) => new Promise(resolve => setTimeout(resolve, milliseconds))
const fail = message => { throw new Error(message) }
try {
  const RefreshRuntime = await import("http://127.0.0.1:${port}/@react-refresh")
  RefreshRuntime.injectIntoGlobalHook(window)
  window.$RefreshReg$ = () => {}
  window.$RefreshSig$ = () => type => type
  window.__vite_plugin_react_preamble_installed__ = true
  const { default: React } = await import("http://127.0.0.1:${port}/@id/react")
  const { default: ReactDOM } = await import("http://127.0.0.1:${port}/@id/react-dom/client")
  const { QuotesSection } = await import("http://127.0.0.1:${port}/src/components/quotes/QuotesSection.tsx")
  const root = ReactDOM.createRoot(document.getElementById("root"))
  const render = bookId => root.render(React.createElement(QuotesSection, { key: bookId, bookId, currentUserId: 7, isAdmin: false }))
  const setDraft = value => {
    const textarea = document.getElementById("new-quote")
    const setValue = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set
    setValue.call(textarea, value)
    textarea.dispatchEvent(new Event("input", { bubbles: true }))
  }

  render(1)
  await wait(50)
  const add = document.querySelector("button")
  if (!add || add.disabled !== true || postCount !== 0) fail("create was not guarded while GET was pending: " + Boolean(add) + " " + add?.disabled + " " + postCount)
  add.click()
  if (postCount !== 0) fail("clicking the disabled create button started a POST")

  gets.get(1).resolve(response([]))
  await wait(); await wait()
  setDraft("race-safe quote")
  await wait(20)
  document.querySelector("button").click()
  await wait(); await wait()
  if (postCount !== 1) fail("expected exactly one POST after GET completed")
  if (document.querySelectorAll("article").length !== 1) fail("created quote card was not rendered")

  setDraft("draft before switching")
  await wait(20)
  if (document.getElementById("new-quote").value !== "draft before switching") fail("draft was not populated before switching")
  render(8)
  await wait(20)
  gets.get(8).reject(new Error("old book load failed"))
  await wait(20)
  if (!document.querySelector("[role=alert]")) fail("blank/error state was not populated before switching")

  render(2)
  await wait(20)
  if (document.querySelectorAll("article").length !== 0) fail("book switch retained prior quote cards")
  if (document.getElementById("new-quote").value !== "") fail("book switch retained the prior draft")
  if (document.querySelector("[role=alert]")) fail("book switch retained the prior error")
  if (!document.querySelector("[role=status]")) fail("book switch did not show loading state")

  render(3)
  await wait(20)
  render(4)
  await wait(20)
  gets.get(3).resolve(response([{ id: 99, book_id: 3, user_id: 7, username: "old", text: "stale" }]))
  await wait(20)
  if (document.querySelectorAll("article").length !== 0) fail("stale success changed the new book cards")
  if (!document.querySelector("[role=status]")) fail("new book stopped loading after stale success")

  render(5)
  await wait(20)
  render(6)
  await wait(20)
  gets.get(5).reject(new Error("stale book error"))
  await wait(20)
  if (document.querySelector("[role=alert]")) fail("stale failure changed the new book error state")
  if (!document.querySelector("[role=status]")) fail("new book stopped loading after stale failure")

  render(7)
  await wait(20)
  root.unmount()
  gets.get(7).resolve(response([{ id: 100, book_id: 7, user_id: 7, username: "unmounted", text: "ignored" }]))
  await wait()
  if (document.getElementById("root").textContent !== "") fail("unmounted request changed the DOM")
  document.getElementById("result").textContent = "PASS"
} catch (error) {
  document.getElementById("result").textContent = "FAIL: " + error.message
}
</script>`
}

test("QuotesSection guards create against the initial GET race and ignores stale requests", async () => {
  const port = 5200 + (process.pid % 500)
  const server = spawn(process.execPath, ["node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", String(port)], {
    cwd: new URL(".", import.meta.url),
    stdio: "ignore",
  })
  try {
    for (let attempt = 0; attempt < 50; attempt++) {
      try {
        await fetch(`http://127.0.0.1:${port}/@id/react`)
        break
      } catch {
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    }
    const url = `data:text/html;charset=utf-8,${encodeURIComponent(pageSource(port))}`
    const { stdout } = await run("/usr/bin/chromium", ["--headless", "--no-sandbox", "--disable-gpu", "--disable-web-security", "--dump-dom", "--virtual-time-budget=3000", url], { timeout: 15000, maxBuffer: 1024 * 1024 })
    assert.match(stdout, /<pre id="result">PASS<\/pre>/, stdout)
  } finally {
    server.kill("SIGTERM")
  }
})
