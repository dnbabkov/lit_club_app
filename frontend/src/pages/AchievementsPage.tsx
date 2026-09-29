import { useLocation, useNavigate, useParams } from "react-router-dom"
import { Layout } from "../components/Layout"
import { ProfileAchievements } from "../components/profile/ProfileAchievements"

export function AchievementsPage() {
  const { username } = useParams<{ username: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const profilePath = username ? `/users/${encodeURIComponent(username)}/profile` : "/profile"
  const backPath = location.state?.from === "achievement-directory" ? "/achievements" : profilePath

  return <Layout>
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 16 }}>
      <button type="button" onClick={() => navigate(backPath)}>← Назад</button>
    </div>
    <h1>Достижения</h1>
    <ProfileAchievements key={username ?? "me"} username={username} />
  </Layout>
}
