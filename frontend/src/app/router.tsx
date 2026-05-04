import {createBrowserRouter} from "react-router-dom";
import {LoginPage} from "../pages/LoginPage"
import {RegisterPage} from "../pages/RegisterPage.tsx";
import {HomePage} from "../pages/HomePage.tsx";
import {MeetingsPage} from "../pages/MeetingsPage.tsx";
import {SelectionPage} from "../pages/SelectionPage.tsx";
import {BooksPage} from "../pages/BooksPage.tsx";
import {BookPage} from "../pages/BookPage.tsx"
import {FinishedBooksPage} from "../pages/FinishedBooksPage.tsx";
import {ProfilePage} from "../pages/ProfilePage.tsx";
import {ProtectedRoute} from "../components/ProtectedRoute.tsx";
import {UsersPage} from "../pages/UsersPage.tsx";

export const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <HomePage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/register",
    element: <RegisterPage />,
  },
  {
    path: "/meetings",
    element: (
      <ProtectedRoute>
        <MeetingsPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/selection",
    element: (
      <ProtectedRoute>
        <SelectionPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/books/finished",
    element: (
      <ProtectedRoute>
        <FinishedBooksPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/books",
    element: (
      <ProtectedRoute>
        <BooksPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/profile",
    element: (
      <ProtectedRoute>
        <ProfilePage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/books/:bookId",
    element: (
      <ProtectedRoute>
        <BookPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/users",
    element: (
        <ProtectedRoute>
          <UsersPage/>
        </ProtectedRoute>
    )
  }
])