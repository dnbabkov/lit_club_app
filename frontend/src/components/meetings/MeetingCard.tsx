import type { MeetingWithBook } from "../../types/meetings"

type MeetingCardProps = {
  meetingWithBook: MeetingWithBook
  isModerator: boolean
  onFinish?: (meetingId: number) => void
  onSchedule?: (meetingId: number) => void
}

function formatMeetingStatus(status: string): string {
  if (status === "book_selection") {
    return "Идёт выбор книги"
  }

  if (status === "scheduled") {
    return "Запланирована"
  }

  if (status === "finished") {
    return "Завершена"
  }

  return status
}

function formatMeetingDate(dateString: string | null): string {
  if (!dateString) {
    return "Дата не назначена"
  }

  const date = new Date(dateString)

  return date.toLocaleString("ru-RU", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function MeetingCard({
  meetingWithBook,
  isModerator,
  onFinish,
  onSchedule,
}: MeetingCardProps) {
  const { meeting, book } = meetingWithBook

  const canScheduleMeeting =
    (meeting.status === "book_selection" && meeting.book_id !== null) ||
    meeting.status === "scheduled"

  const canFinishMeeting = meeting.status === "scheduled"

  const scheduleButtonText =
    meeting.status === "book_selection"
      ? "Назначить дату и время встречи"
      : "Изменить дату и время встречи"

  function handleFinishClick() {
    if (!onFinish) return

    const confirmed = window.confirm(
      "Вы уверены, что хотите завершить эту встречу?"
    )

    if (!confirmed) {
      return
    }

    onFinish(meeting.id)
  }

  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 16,
        marginBottom: 16,
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: 12 }}>
        Встреча #{meeting.id}
      </h3>

      <p style={{ margin: "4px 0" }}>
        <strong>Статус:</strong> {formatMeetingStatus(meeting.status)}
      </p>

      <p style={{ margin: "4px 0" }}>
        <strong>Дата:</strong> {formatMeetingDate(meeting.scheduled_for)}
      </p>

      <div style={{ marginTop: 12 }}>
        <strong>Книга:</strong>
        {book ? (
          <div style={{ marginTop: 4 }}>
            <div>{book.title}</div>
            <div style={{ color: "#555", fontSize: 14 }}>{book.author}</div>
          </div>
        ) : (
          <div style={{ marginTop: 4, color: "#777" }}>
            Книга пока не назначена
          </div>
        )}
      </div>

      {isModerator && (canScheduleMeeting || canFinishMeeting) && (
        <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
          {onSchedule && canScheduleMeeting && (
            <button type="button" onClick={() => onSchedule(meeting.id)}>
              {scheduleButtonText}
            </button>
          )}

          {onFinish && canFinishMeeting && (
            <button type="button" onClick={handleFinishClick}>
              Завершить встречу
            </button>
          )}
        </div>
      )}
    </div>
  )
}