import { Navigate } from "react-router-dom"
import { useAuth } from "../auth/AuthContext"
import { Layout } from "../components/Layout.tsx";

export function HomePage(){
    const { isAuthenticated } = useAuth()

    if (!isAuthenticated){
        return <Navigate to="/login" replace />
    }

    return (
    <Layout>
      <h1>Главная</h1>
      <p>Добро пожаловать в приложение литературного клуба.</p>
      <p>Здесь позже появится актуальная информация о встречах и выборе книги.</p>
    </Layout>
  )
}