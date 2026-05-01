import { Link } from "react-router-dom";
import {useAuth} from "../auth/AuthContext.tsx";

export function NavBar() {
    const { isAuthenticated, logout } = useAuth()

    return (
        <header
          style={{
            borderBottom: "1px solid #ddd",
            padding: "16px 24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <Link to="/" style={{ fontWeight: "bold", textDecoration: "none", color: "black" }}>
              Литературный клуб
            </Link>
          </div>

          <nav style={{ display: "flex", gap: 16, alignItems: "center" }}>
            {isAuthenticated ? (
              <>
                <Link to="/meetings">Встречи</Link>
                <Link to="/selection">Выбор книги</Link>
                <Link to="/books/finished">Прочитанные книги</Link>
                <Link to="/books">Все книги</Link>
                <Link to="/profile">Профиль</Link>
                <button onClick={logout}>Выйти</button>
              </>
            ) : (
              <>
                <Link to="/login">Войти</Link>
                <Link to="/register">Регистрация</Link>
              </>
            )}
          </nav>
        </header>
    )
}