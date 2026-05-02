import { useCallback, useEffect, useState } from "react"
import { Layout } from "../components/Layout"
import { ApiError } from "../api/http"
import { getMyProfile } from "../api/profile"
import { ProfileBookCard } from "../components/profile/ProfileBookCard"
import type { UserProfileRead } from "../types/profile"

export function ProfilePage() {
  const [profile, setProfile] = useState<UserProfileRead | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")

  const loadProfileData = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")

    try {
      const data = await getMyProfile()
      setProfile(data)
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProfileData()
  }, [loadProfileData])

  return (
    <Layout>
      <h1>Профиль</h1>

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && profile && (
        <>
          <div
            style={{
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: 16,
              marginBottom: 24,
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 12 }}>
              {profile.username}
            </h2>

            <p style={{ margin: "4px 0" }}>
              <strong>Telegram login:</strong> {profile.telegram_login}
            </p>

            <p style={{ margin: "4px 0" }}>
              <strong>Роль:</strong>{" "}
              {profile.role === "moderator" ? "Модератор" : "Участник"}
            </p>
          </div>

          <div>
            <h2>Предложенные книги</h2>

            {profile.nominated_books.length === 0 ? (
              <p>Вы пока не предлагали ни одной книги.</p>
            ) : (
              profile.nominated_books.map((item) => (
                <ProfileBookCard key={item.book_id} item={item} />
              ))
            )}
          </div>
        </>
      )}
    </Layout>
  )
}