import { useCallback, useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Layout } from "../components/Layout"
import { useAuth } from "../auth/AuthContext"
import { ApiError } from "../api/http"
import { getBooks } from "../api/books"
import { finishMeeting, getMeetings, startNextMeeting } from "../api/meetings"
import { MeetingCard } from "../components/meetings/MeetingCard"
import { ScheduleMeetingForm } from "../components/meetings/ScheduleMeetingForm"
import type { BookRead } from "../types/books"
import type { MeetingWithBook } from "../types/meetings"

export function MeetingsPage() {
  const navigate = useNavigate()
  const { user } = useAuth()

  const [meetingsWithBooks, setMeetingsWithBooks] = useState<MeetingWithBook[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [schedulingMeetingId, setSchedulingMeetingId] = useState<number | null>(null)

  const isModerator = user?.role === "moderator"

  const loadMeetingsData = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")

    try {
      const meetings = await getMeetings()
      const booksResponse = await getBooks()

      const booksById = new Map<number, BookRead>(
        booksResponse.books.map((item) => [item.book.id, item.book])
      )

      const combined: MeetingWithBook[] = meetings.map((meeting) => ({
        meeting,
        book:
          meeting.book_id !== null
            ? booksById.get(meeting.book_id) ?? null
            : null,
      }))

      setMeetingsWithBooks(combined)
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
    loadMeetingsData()
  }, [loadMeetingsData])

  async function handleStartNext() {
    setIsSubmitting(true)
    setErrorMessage("")

    try {
      await startNextMeeting()
      await loadMeetingsData()
      navigate("/selection")
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleFinishMeeting(meetingId: number) {
    setIsSubmitting(true)
    setErrorMessage("")

    try {
      await finishMeeting(meetingId)
      await loadMeetingsData()
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleOpenSchedule(meetingId: number) {
    setSchedulingMeetingId((prev) => (prev === meetingId ? null : meetingId))
  }

  const latestMeeting =
    meetingsWithBooks.length > 0 ? meetingsWithBooks[0].meeting : null

  const canStartNextCycle =
    isModerator &&
    (latestMeeting === null || latestMeeting.status !== "book_selection")

  return (
    <Layout>
      <h1>Встречи</h1>

      {canStartNextCycle && (
        <div style={{ marginBottom: 24 }}>
          <button type="button" onClick={handleStartNext} disabled={isSubmitting}>
            {isSubmitting ? "Создаём..." : "Начать следующий цикл"}
          </button>
        </div>
      )}

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && meetingsWithBooks.length === 0 && (
        <p>Пока нет ни одной встречи.</p>
      )}

      {!isLoading && !errorMessage && meetingsWithBooks.length > 0 && (
        <div>
          {meetingsWithBooks.map((meetingWithBook) => (
            <div key={meetingWithBook.meeting.id}>
              <MeetingCard
                meetingWithBook={meetingWithBook}
                isModerator={isModerator}
                onFinish={handleFinishMeeting}
                onSchedule={handleOpenSchedule}
              />

              {schedulingMeetingId === meetingWithBook.meeting.id && (
                <ScheduleMeetingForm
                  meetingId={meetingWithBook.meeting.id}
                  onSuccess={async () => {
                    setSchedulingMeetingId(null)
                    await loadMeetingsData()
                  }}
                />
              )}
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}