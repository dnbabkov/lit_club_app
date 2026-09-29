import {createBrowserRouter, Navigate} from "react-router-dom";
import {HomePage} from "../pages/HomePage.tsx";
import {MeetingsPage} from "../pages/MeetingsPage.tsx";
import {SelectionPage} from "../pages/SelectionPage.tsx";
import {BooksPage} from "../pages/BooksPage.tsx";
import {BookPage} from "../pages/BookPage.tsx"
import {FinishedBooksPage} from "../pages/FinishedBooksPage.tsx";
import {ProfilePage} from "../pages/ProfilePage.tsx";
import {AchievementsPage} from "../pages/AchievementsPage.tsx";
import {AchievementDirectoryPage} from "../pages/AchievementDirectoryPage.tsx";
import {ProtectedRoute} from "../components/ProtectedRoute.tsx";
import {UsersPage} from "../pages/UsersPage.tsx";
import {ComicsPage, ComicReaderPage} from "../pages/ComicPage.tsx";
import {ComicEditorPage} from "../pages/ComicEditorPage.tsx";

export const router = createBrowserRouter([
  { path: "/profile/achievements", element: <ProtectedRoute><AchievementsPage /></ProtectedRoute> },
  { path: "/users/:username/profile/achievements", element: <ProtectedRoute><AchievementsPage /></ProtectedRoute> },
  { path: "/achievements", element: <ProtectedRoute><AchievementDirectoryPage /></ProtectedRoute> },
  { path: "/comics", element: <ProtectedRoute><ComicsPage /></ProtectedRoute> },
  { path: "/comics/new", element: <ProtectedRoute><ComicEditorPage /></ProtectedRoute> },
  { path: "/comics/:chapterId", element: <ProtectedRoute><ComicReaderPage /></ProtectedRoute> },
  { path: "/comics/:chapterId/edit", element: <ProtectedRoute><ComicEditorPage /></ProtectedRoute> },
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
    element: <Navigate to="/" replace />,
  },
  {
    path: "/register",
    element: <Navigate to="/" replace />,
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
  },
  {
    path: "/users/:username/profile",
    element: (
        <ProtectedRoute>
          <ProfilePage/>
        </ProtectedRoute>
    )
  }
])
