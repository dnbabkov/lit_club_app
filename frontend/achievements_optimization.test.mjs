import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

const achievementsPage = await readFile(new URL("src/pages/AchievementsPage.tsx", import.meta.url), "utf8")
const profileAchievements = await readFile(new URL("src/components/profile/ProfileAchievements.tsx", import.meta.url), "utf8")

test("AchievementsPage renders navigation shell before ProfileAchievements", async () => {
  assert.match(achievementsPage, /<h1>Достижения<\/h1>[\s\S]*<ProfileAchievements/)
  assert.match(achievementsPage, /<button type="button" onClick=\{\(\) => navigate\(backPath\)\}/)
})

test("achievement images load only as cards approach the viewport", () => {
  assert.match(profileAchievements, /new IntersectionObserver/)
  assert.match(profileAchievements, /rootMargin: "200px"/)
  assert.match(profileAchievements, /getAchievementImage\(achievement\.image_url, controller\.signal\)/)
  assert.match(profileAchievements, /Загрузка ачивки/)
  assert.match(profileAchievements, /Повторить/)
})

test("achievement metadata shell is rendered before image content", () => {
  const profileSource = profileAchievements.slice(profileAchievements.indexOf("export function ProfileAchievements"))
  const metadataIndex = profileSource.indexOf("<h2 id=\"profile-achievements-title\">")
  const imageIndex = profileSource.indexOf("achievements.map")
  assert.ok(metadataIndex >= 0)
  assert.ok(imageIndex > metadataIndex)
  assert.match(profileSource, /achievements === null \? <p role="status">Загрузка достижений…/)
})
