import { useNavigate, useParams } from "react-router-dom"
import { Layout } from "../components/Layout"
import { ProfileAchievements } from "../components/profile/ProfileAchievements"

export function AchievementsPage() {
  const { username } = useParams<{ username: string }>()
  const navigate = useNavigate()
  const profilePath = username ? `/users/${encodeURIComponent(username)}/profile` : "/profile"

  return <Layout>
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 16 }}>
      <button type="button" onClick={() => navigate(profilePath)}>← Назад</button>
    </div>
    <ProfileAchievements key={username ?? "me"} username={username} />
  </Layout>
}
