import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

const directorySource = () => readFile(new URL("src/pages/AchievementDirectoryPage.tsx", import.meta.url), "utf8")
const achievementsSource = () => readFile(new URL("src/pages/AchievementsPage.tsx", import.meta.url), "utf8")
const navSource = () => readFile(new URL("src/components/NavBar.tsx", import.meta.url), "utf8")

test("achievement directory uses the required stable Russian/current-user ordering", async () => {
  const source = await directorySource()
  const collator = new Intl.Collator("ru", { sensitivity: "base" })
  const users = [
    { id: 9, username: "Яна" }, { id: 7, username: "Анна" },
    { id: 5, username: "viewer" }, { id: 8, username: "анна" },
  ]
  const currentId = 5
  const ordered = [...users].sort((left, right) => {
    if (left.id === right.id) return 0
    if (left.id === currentId) return -1
    if (right.id === currentId) return 1
    return collator.compare(left.username, right.username) || left.id - right.id
  })
  assert.deepEqual(ordered.map(user => user.username), ["viewer", "Анна", "анна", "Яна"])
  assert.match(source, /new Intl\.Collator\("ru", \{ sensitivity: "base" \}\)/)
  assert.match(source, /left\.id - right\.id/)
  assert.match(source, /left\.id === currentUser\?\.id/)
})

test("achievement directory never re-injects dev_admin, including when it is the current user", async () => {
  const source = await directorySource()
  const apiUsers = [
    { id: 1, username: "dev_admin" },
    { id: 2, username: "viewer" },
  ]
  const currentUser = apiUsers[0]
  const visibleUsers = apiUsers.filter(user => user.username !== "dev_admin")

  assert.deepEqual(visibleUsers, [{ id: 2, username: "viewer" }])
  assert.match(source, /setUsers\(data\.filter\(user => user\.username !== "dev_admin"\)\)/)
  assert.doesNotMatch(source, /setUsers\([^\n]*currentUser/)
  assert.equal(visibleUsers.some(user => user.id === currentUser.id), false)
})

test("achievement directory routing preserves the directory origin and safe identifiers", async () => {
  const [directory, achievements] = await Promise.all([directorySource(), achievementsSource()])
  assert.match(directory, /encodeURIComponent\(user\.username\)/)
  assert.match(directory, /state: \{ from: "achievement-directory" \}/)
  assert.match(achievements, /location\.state\?\.from === "achievement-directory" \? "\/achievements"/)
  assert.match(achievements, /encodeURIComponent\(username\)/)
})

test("authenticated navigation keeps achievements for every role and admin Users link", async () => {
  const source = await navSource()
  assert.match(source, /\{isAuthenticated \? \(/)
  assert.match(source, /to="\/achievements"[\s\S]*Ачивки/)
  assert.match(source, /user\?\.role === "admin"[\s\S]*to="\/users"/)
})
