import assert from "node:assert/strict"
import { after, test } from "node:test"
import { createServer } from "vite"

const server = await createServer({ server: { middlewareMode: true }, appType: "custom" })
const tokens = await server.ssrLoadModule("/src/auth/token.ts")
const http = await server.ssrLoadModule("/src/api/http.ts")
const auth = await server.ssrLoadModule("/src/api/auth.ts")
after(() => server.close())

test("Telegram login sends raw initData without a previous bearer token", async () => {
  const originalFetch = globalThis.fetch
  tokens.setToken("old-session")
  globalThis.fetch = async (url, options) => {
    assert.ok(url.endsWith("/users/auth/telegram"))
    assert.equal(options.headers.Authorization, undefined)
    assert.deepEqual(JSON.parse(options.body), { init_data: "user=%7B%7D&hash=test" })
    return Response.json({ access_token: "new-session", token_type: "bearer" })
  }
  try {
    assert.equal((await auth.loginTelegram("user=%7B%7D&hash=test")).access_token, "new-session")
  } finally {
    globalThis.fetch = originalFetch
    tokens.removeToken()
  }
})

test("expired and revoked sessions notify the provider, ordinary role denials do not", async () => {
  const originalFetch = globalThis.fetch
  const failures = []
  const unsubscribe = tokens.onSessionFailure(status => failures.push(status))
  try {
    for (const [status, detail, invalidated] of [
      [403, "Only admin can perform this action", false],
      [401, "Invalid credentials", true],
      [403, "Access not granted", true],
    ]) {
      tokens.setToken("session")
      globalThis.fetch = async () => Response.json({ detail }, { status })
      await assert.rejects(http.get("/users/me"), error => error.status === status)
      assert.equal(tokens.getToken(), invalidated ? null : "session")
    }
    assert.deepEqual(failures, [401, 403])
  } finally {
    unsubscribe()
    globalThis.fetch = originalFetch
    tokens.removeToken()
  }
})

test("late responses from an old session cannot invalidate the current session", () => {
  tokens.setToken("current-session")
  tokens.reportSessionFailure("old-session", 401, "Invalid credentials")
  assert.equal(tokens.getToken(), "current-session")
  tokens.removeToken()
})
