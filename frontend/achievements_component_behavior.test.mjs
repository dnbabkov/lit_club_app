import assert from "node:assert/strict"
import { execFile, spawn } from "node:child_process"
import { promisify } from "node:util"
import { test } from "node:test"

const run = promisify(execFile)

function pageSource(port) {
  return `<!doctype html><meta charset="utf-8"><div id="root"></div><pre id="result">running</pre>
<script type="module">
const requests = []
let deleted = false
let deleteMode = "success"
window.fetch = async (input, init = {}) => {
  const path = String(input), method = init.method || "GET"
  requests.push({ path, method })
  if (path.endsWith("/users/me/profile/achievements") && method === "GET") return { ok: true, status: 200, json: async () => deleted ? [] : [{ id: 1, image_url: "/achievements/1/image", giver: { id: 7, username: "giver" }, title: "Award", description: "Description" }] }
  if (path.endsWith("/image") && method === "GET") return new Response(new Blob(["image"]), { status: 200, headers: { "Content-Type": "image/png" } })
  if (path.match(/\\/achievements\\/\\d+$/) && method === "DELETE") {
    if (deleteMode === "failure") return { ok: false, status: 500, json: async () => ({ detail: "delete failed" }) }
    deleted = true; return { ok: true, status: 204, json: async () => null }
  }
  throw new Error("unexpected request " + method + " " + path)
}
const wait = (milliseconds = 0) => new Promise(resolve => setTimeout(resolve, milliseconds)); async function settle() { await wait(); await wait(50) }; const fail = message => { throw new Error(message) }
try {
  const RefreshRuntime = await import("http://127.0.0.1:${port}/@react-refresh"); RefreshRuntime.injectIntoGlobalHook(window); window.$RefreshReg$ = () => {}; window.$RefreshSig$ = () => type => type; window.__vite_plugin_react_preamble_installed__ = true
  const { default: React } = await import("http://127.0.0.1:${port}/@id/react"); const { default: ReactDOM } = await import("http://127.0.0.1:${port}/@id/react-dom/client"); const { AuthContext } = await import("http://127.0.0.1:${port}/src/auth/context.ts"); const { ProfileAchievements } = await import("http://127.0.0.1:${port}/src/components/profile/ProfileAchievements.tsx")
  const root = ReactDOM.createRoot(document.getElementById("root")); const auth = user => ({ user, status: "authenticated", isAuthenticated: true, retry: () => {} }); const render = user => root.render(React.createElement(AuthContext.Provider, { value: auth(user) }, React.createElement(ProfileAchievements, { key: user.id + ":" + user.role })))
  render({ id: 7, username: "giver", role: "member" }); await settle(); const ownerDelete = [...document.querySelectorAll("button")].find(button => button.textContent.includes("Удалить")); if (!ownerDelete) fail("giver cannot delete")
  window.confirm = () => false; ownerDelete.click(); await settle(); if (requests.some(request => request.method === "DELETE")) fail("cancelled delete sent request")
  window.confirm = () => true; ownerDelete.click(); await settle(); if (requests.filter(request => request.method === "DELETE").length !== 1) fail("owner delete request missing"); if (!document.body.textContent.includes("У вас пока нет достижений.")) fail("successful delete did not refresh")
  deleted = false; render({ id: 9, username: "recipient", role: "member" }); await settle(); if ([...document.querySelectorAll("button")].some(button => button.textContent.includes("Удалить"))) fail("recipient can delete")
  render({ id: 99, username: "admin", role: "admin" }); await settle(); const adminDelete = [...document.querySelectorAll("button")].find(button => button.textContent.includes("Удалить")); if (!adminDelete) fail("admin cannot delete"); deleteMode = "failure"; window.confirm = () => true; adminDelete.click(); await settle(); if (![...document.querySelectorAll("[role=alert]")].some(alert => alert.textContent.includes("delete failed"))) fail("delete failure was hidden")
  document.getElementById("result").textContent = "PASS"
} catch (error) { document.getElementById("result").textContent = "FAIL: " + error.message }
</script>`
}

test("ProfileAchievements owner/admin deletion and recipient denial work in Chromium", async () => {
  const port = 5300 + (process.pid % 400); const server = spawn(process.execPath, ["node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", String(port)], { cwd: new URL(".", import.meta.url), stdio: "ignore" })
  try {
    for (let attempt = 0; attempt < 50; attempt++) { try { await fetch(`http://127.0.0.1:${port}/@id/react`); break } catch { await new Promise(resolve => setTimeout(resolve, 100)) } }
    const url = `data:text/html;charset=utf-8,${encodeURIComponent(pageSource(port))}`; const { stdout } = await run("/usr/bin/chromium", ["--headless", "--no-sandbox", "--disable-gpu", "--disable-web-security", "--dump-dom", "--virtual-time-budget=4000", url], { timeout: 15000, maxBuffer: 1024 * 1024 }); assert.match(stdout, /<pre id="result">PASS<\/pre>/, stdout)
  } finally { server.kill("SIGTERM") }
})
