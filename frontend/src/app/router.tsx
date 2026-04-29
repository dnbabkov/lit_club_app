import { createBrowserRouter } from "react-router-dom";
import { LoginPage } from "../pages/LoginPage"

function HomePage() {
    return <div>Frontend is running</div>
}

export const router = createBrowserRouter([
    {
        path: "/",
        element: <HomePage />
    },
    {
        path: "/login",
        element: <LoginPage />
    },
])