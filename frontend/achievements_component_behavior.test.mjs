import assert from "node:assert/strict"
import { execFile, spawn } from "node:child_process"
import { promisify } from "node:util"
import { test } from "node:test"

const run = promisify(execFile)

function pageSource(port) {
  return `<!doctype html><meta charset="utf-8"><div id="root"></div><pre id="result">running</pre>
<script type="module">
const requests = []
const deleted = new Set()
let deleteMode = "success"
let deleteRequest = null
const profiles = {
  me: [{ id: 1, image_url: "/achievements/1/image", giver: { id: 7, username: "giver" }, title: "Award", description: "Description" }],
  recipient: [{ id: 2, image_url: "/achievements/2/image", giver: { id: 7, username: "giver" }, title: "Recipient award", description: "Description" }],
  other: [{ id: 3, image_url: "/achievements/3/image", giver: { id: 7, username: "giver" }, title: "Other award", description: "Description" }],
}
const response = (data, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => data })
window.fetch = async (input, init = {}) => {
  const path = String(input), method = init.method || "GET"
  requests.push({ path, method })
  if (method === "GET" && path.includes("/profile/achievements")) {
    const profile = path.includes("/users/me/") ? "me" : decodeURIComponent(path.split("/users/")[1].split("/profile")[0])
    return response((profiles[profile] || []).filter(achievement => !deleted.has(achievement.id)))
  }
  if (path.endsWith("/image") && method === "GET") return new Response(new Blob(["image"]), { status: 200, headers: { "Content-Type": "image/png" } })
  if (path.match(/\\/achievements\\/\\d+$/) && method === "DELETE") {
    deleteRequest = {}
    if (deleteMode === "failure") return response({ detail: "delete failed" }, 500)
    await new Promise(resolve => { deleteRequest.resolve = resolve })
    deleted.add(Number(path.match(/\\d+$/)[0]))
    return response(null, 204)
  }
  throw new Error("unexpected request " + method + " " + path)
}
const wait = (milliseconds = 0) => new Promise(resolve => setTimeout(resolve, milliseconds))
async function settle() { await wait(); await wait(50) }
async function until(predicate, message) { for (let attempt = 0; attempt < 40; attempt++) { if (predicate()) return; await wait(25) }; throw new Error(message) }
const fail = message => { throw new Error(message) }
const buttons = text => [...document.querySelectorAll("button")].filter(button => button.textContent.includes(text))
const deleteButton = () => buttons("Удалить ачивку")[0]
const confirmButton = () => buttons("Подтвердить удаление")[0]
try {
  const RefreshRuntime = await import("http://127.0.0.1:${port}/@react-refresh"); RefreshRuntime.injectIntoGlobalHook(window); window.$RefreshReg$ = () => {}; window.$RefreshSig$ = () => type => type; window.__vite_plugin_react_preamble_installed__ = true
  const { default: React } = await import("http://127.0.0.1:${port}/@id/react"); const { default: ReactDOM } = await import("http://127.0.0.1:${port}/@id/react-dom/client"); const { AuthContext } = await import("http://127.0.0.1:${port}/src/auth/context.ts"); const { ProfileAchievements } = await import("http://127.0.0.1:${port}/src/components/profile/ProfileAchievements.tsx")
  const root = ReactDOM.createRoot(document.getElementById("root")); const auth = user => ({ user, status: "authenticated", isAuthenticated: true, retry: () => {} }); const render = (user, username) => root.render(React.createElement(AuthContext.Provider, { value: auth(user) }, React.createElement(ProfileAchievements, { username, key: user.id + ":" + user.role + ":" + username })))
  window.confirm = () => { throw new Error("native confirm must not be called") }
  render({ id: 7, username: "giver", role: "member" }); await until(() => deleteButton(), "giver cannot delete")
  const ownerDelete = deleteButton(); ownerDelete.click(); await settle(); if (!document.querySelector("[role=alertdialog]")) fail("first click did not show confirmation"); if (requests.some(request => request.method === "DELETE")) fail("first click sent delete request")
  buttons("Отмена")[0].click(); await settle(); if (document.querySelector("[role=alertdialog]")) fail("cancel did not close confirmation"); if (requests.some(request => request.method === "DELETE")) fail("cancelled delete sent request")
  deleteMode = "failure"; ownerDelete.click(); await settle(); confirmButton().click(); await until(() => [...document.querySelectorAll("[role=alert]")].some(alert => alert.textContent.includes("delete failed")), "delete failure was hidden"); deleteMode = "success"
  const ownerDeleteCount = requests.filter(request => request.method === "DELETE").length; deleteRequest = null; ownerDelete.click(); await settle(); const ownerConfirm = confirmButton(); ownerConfirm.click(); await until(() => deleteRequest, "owner delete request missing"); if (requests.filter(request => request.method === "DELETE").length !== ownerDeleteCount + 1) fail("owner delete request count wrong")
  ownerConfirm.click(); if (requests.filter(request => request.method === "DELETE").length !== ownerDeleteCount + 1) fail("duplicate confirmation sent request")
  deleteRequest.resolve(); await until(() => document.body.textContent.includes("У вас пока нет достижений."), "successful owner delete did not refresh")
  render({ id: 9, username: "recipient", role: "member" }, "recipient"); await until(() => document.body.textContent.includes("Recipient award"), "recipient profile did not load"); if (deleteButton()) fail("recipient can delete")
  render({ id: 99, username: "admin", role: "admin" }, "recipient"); await until(() => deleteButton(), "admin cannot delete"); deleteButton().click(); await settle(); if (!document.querySelector("[role=alertdialog]")) fail("admin confirmation missing"); deleteRequest = null; confirmButton().click(); await until(() => deleteRequest, "admin delete request missing"); deleteRequest.resolve(); await until(() => document.body.textContent.includes("У пользователя пока нет достижений."), "successful admin delete did not refresh")
  render({ id: 99, username: "admin", role: "admin" }, "other"); await until(() => document.body.textContent.includes("Other award"), "profile switch did not load new profile")
  document.getElementById("result").textContent = "PASS"
} catch (error) { document.getElementById("result").textContent = "FAIL: " + error.message }
</script>`
}

test("ProfileAchievements uses in-app confirmation and protects authorized deletion in Chromium", async () => {
  const port = 5300 + (process.pid % 400); const server = spawn(process.execPath, ["node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", String(port)], { cwd: new URL(".", import.meta.url), stdio: "ignore" })
  try {
    for (let attempt = 0; attempt < 50; attempt++) { try { await fetch(`http://127.0.0.1:${port}/@id/react`); break } catch { await new Promise(resolve => setTimeout(resolve, 100)) } }
    const url = `data:text/html;charset=utf-8,${encodeURIComponent(pageSource(port))}`; const { stdout } = await run("/usr/bin/chromium", ["--headless", "--no-sandbox", "--disable-gpu", "--disable-web-security", "--dump-dom", "--virtual-time-budget=6000", url], { timeout: 15000, maxBuffer: 1024 * 1024 }); assert.match(stdout, /<pre id="result">PASS<\/pre>/, stdout)
  } finally { server.kill("SIGTERM") }
})
